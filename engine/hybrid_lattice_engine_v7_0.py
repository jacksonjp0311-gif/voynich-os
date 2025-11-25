#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v7.0 — Hybrid Lattice Engine (Glyph Seeds → Lattice → Bands)
# Auto-written by All-One PS (v7.0)

import os
import json
import math
import datetime

VERSION = "v7_0"

# ─────────────────────────────
# Basic helpers
# ─────────────────────────────

def now_utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_json(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_jsonl(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def safe_stats(values):
    vals = [float(v) for v in values]
    if not vals:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(sum(vals) / len(vals)),
        "min": float(min(vals)),
        "max": float(max(vals)),
    }

# ─────────────────────────────
# Load v6.1 expansion
# ─────────────────────────────

def build_stub_expansion():
    # Minimal stub compatible with v6.1 structure
    return {
        "version": "v6_1_stub",
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": {},
        "pages": [
            {
                "page_id": "GLOBAL_PAGE",
                "num_glyph_seeds": 4,
                "glyph_seed_ids": [
                    "GLOBAL_PAGE_g000",
                    "GLOBAL_PAGE_g001",
                    "GLOBAL_PAGE_g002",
                    "GLOBAL_PAGE_g003",
                ],
                "glyph_grid_score": 1.0,
                "coverage_ratio": 1.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
                "hybrid_eva_tokens": 0,
                "hybrid_takahashi_tokens": 0,
                "hybrid_delta_tokens": 0,
            }
        ],
        "glyph_seeds": [
            {
                "glyph_id": "GLOBAL_PAGE_g000",
                "page_id": "GLOBAL_PAGE",
                "fields": ["meta"],
                "rank_in_page": 0,
                "normalized_index": 0.125,
                "intensity": 1.0,
                "coverage_ratio": 1.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
            },
            {
                "glyph_id": "GLOBAL_PAGE_g001",
                "page_id": "GLOBAL_PAGE",
                "fields": ["meta"],
                "rank_in_page": 1,
                "normalized_index": 0.375,
                "intensity": 2.0,
                "coverage_ratio": 1.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
            },
            {
                "glyph_id": "GLOBAL_PAGE_g002",
                "page_id": "GLOBAL_PAGE",
                "fields": ["meta"],
                "rank_in_page": 2,
                "normalized_index": 0.625,
                "intensity": 2.0,
                "coverage_ratio": 1.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
            },
            {
                "glyph_id": "GLOBAL_PAGE_g003",
                "page_id": "GLOBAL_PAGE",
                "fields": ["meta"],
                "rank_in_page": 3,
                "normalized_index": 0.875,
                "intensity": 1.0,
                "coverage_ratio": 1.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
            },
        ],
        "fields": [
            {
                "field_id": "meta",
                "num_pages": 1,
                "page_ids": ["GLOBAL_PAGE"],
                "delta_phi_field": 0.0,
                "field_resonance_index": 0.0,
            }
        ],
    }

def load_expansion(path):
    data = load_json(path, default=None)
    if not data or "pages" not in data or "glyph_seeds" not in data:
        data = build_stub_expansion()
    return data

# ─────────────────────────────
# Lattice construction
# ─────────────────────────────

def build_page_to_seeds(seeds):
    mapping = {}
    for s in seeds:
        pid = str(s.get("page_id", "")) or "UNKNOWN_PAGE"
        if pid not in mapping:
            mapping[pid] = []
        mapping[pid].append(s)
    return mapping

def build_lattice(expansion_obj):
    pages  = expansion_obj.get("pages", [])
    seeds  = expansion_obj.get("glyph_seeds", [])
    fields = expansion_obj.get("fields", [])
    glyph_seed_meta = expansion_obj.get("glyph_seed", {})

    page_to_seeds = build_page_to_seeds(seeds)

    nodes = []
    edges = []
    pages_lattice = []

    # Node lookup to accumulate degrees / gradients
    node_neighbors = {}

    edge_counter = 0

    for p in pages:
        pid = str(p.get("page_id", "")) or "UNKNOWN_PAGE"

        cov   = float(p.get("coverage_ratio", 0.0))
        coh   = float(p.get("coherence_index", 0.0))
        dphi  = float(p.get("delta_phi_mean", 0.0))
        ggrid = float(p.get("glyph_grid_score", 0.0))

        page_seeds = list(page_to_seeds.get(pid, []))
        if not page_seeds:
            continue

        # Sort seeds by normalized index around the page ring
        page_seeds.sort(key=lambda s: float(s.get("normalized_index", 0.0)))

        # Create initial node entries
        for s in page_seeds:
            gid = str(s.get("glyph_id", ""))
            node = {
                "glyph_id": gid,
                "page_id": pid,
                "fields": list(s.get("fields", [])),
                "rank_in_page": int(s.get("rank_in_page", 0)),
                "normalized_index": float(s.get("normalized_index", 0.0)),
                "intensity": float(s.get("intensity", 0.0)),
                "coverage_ratio": float(s.get("coverage_ratio", cov)),
                "coherence_index": float(s.get("coherence_index", coh)),
                "delta_phi_mean": float(s.get("delta_phi_mean", dphi)),
                "degree": 0,
                "local_gradient": 0.0,
            }
            nodes.append(node)
            node_neighbors[gid] = []

        # Build ring edges on this page
        n = len(page_seeds)
        if n >= 2:
            for i in range(n):
                a = page_seeds[i]
                b = page_seeds[(i + 1) % n]  # ring closure

                gid_a = str(a.get("glyph_id", ""))
                gid_b = str(b.get("glyph_id", ""))

                ia = float(a.get("intensity", 0.0))
                ib = float(b.get("intensity", 0.0))

                ta = float(a.get("normalized_index", 0.0))
                tb = float(b.get("normalized_index", 0.0))

                w_intensity = abs(ia - ib)
                phase_dist = abs(tb - ta)

                edge_id = f"{pid}_e{str(edge_counter).zfill(4)}"
                edge_counter += 1

                edge = {
                    "edge_id": edge_id,
                    "page_id": pid,
                    "glyph_a": gid_a,
                    "glyph_b": gid_b,
                    "intensity_a": ia,
                    "intensity_b": ib,
                    "weight_intensity": float(w_intensity),
                    "phase_distance": float(phase_dist),
                    "mean_intensity": float(0.5 * (ia + ib)),
                }
                edges.append(edge)

                node_neighbors[gid_a].append((gid_b, w_intensity))
                node_neighbors[gid_b].append((gid_a, w_intensity))

        # Page-level lattice metrics (simple harmonic index approximation)
        intensities = [float(s.get("intensity", 0.0)) for s in page_seeds]
        if intensities:
            imin = min(intensities)
            imax = max(intensities)
            irange = max(imax - imin, 0.0)
            lattice_harmonic_index = 1.0 / (1.0 + irange)
        else:
            lattice_harmonic_index = 0.0

        pages_lattice.append({
            "page_id": pid,
            "num_glyph_seeds": n,
            "glyph_grid_score": ggrid,
            "coverage_ratio": cov,
            "coherence_index": coh,
            "delta_phi_mean": dphi,
            "lattice_harmonic_index": float(lattice_harmonic_index),
        })

    # Compute degree and local gradient per node
    node_index = {n["glyph_id"]: n for n in nodes}
    for gid, neighbors in node_neighbors.items():
        node = node_index.get(gid)
        if not node:
            continue
        deg = len(neighbors)
        node["degree"] = int(deg)
        if deg == 0:
            node["local_gradient"] = 0.0
        else:
            base_intensity = float(node.get("intensity", 0.0))
            diffs = [abs(base_intensity - neighbor_weighted) for (_, neighbor_weighted) in []]  # placeholder

            # Actually use neighbor intensity difference from the stored weights
            diffs = [float(w) for (_, w) in neighbors]
            node["local_gradient"] = float(sum(diffs) / len(diffs)) if diffs else 0.0

    lattice_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "pages_lattice": pages_lattice,
        "fields": fields,
    }
    return lattice_obj

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_lattice(lattice_obj):
    nodes = lattice_obj.get("nodes", [])
    edges = lattice_obj.get("edges", [])
    pages_lattice = lattice_obj.get("pages_lattice", [])
    fields = lattice_obj.get("fields", [])

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_nodes": lattice_obj.get("num_nodes", len(nodes)),
        "num_edges": lattice_obj.get("num_edges", len(edges)),
        "num_pages": len(pages_lattice),
        "num_fields": len(fields),
        "glyph_seed": lattice_obj.get("glyph_seed", {}),
    }

    intensities = [n["intensity"] for n in nodes] if nodes else []
    degrees     = [n["degree"] for n in nodes] if nodes else []
    gradients   = [n["local_gradient"] for n in nodes] if nodes else []

    weights     = [e["weight_intensity"] for e in edges] if edges else []
    phase_dist  = [e["phase_distance"] for e in edges] if edges else []

    harmonic_idx = [p["lattice_harmonic_index"] for p in pages_lattice] if pages_lattice else []

    summary["nodes"] = {
        "intensity": safe_stats(intensities),
        "degree": safe_stats(degrees),
        "local_gradient": safe_stats(gradients),
    }

    summary["edges"] = {
        "weight_intensity": safe_stats(weights),
        "phase_distance": safe_stats(phase_dist),
    }

    summary["pages"] = {
        "lattice_harmonic_index": safe_stats(harmonic_idx),
    }

    field_pages = [f.get("num_pages", 0) for f in fields]
    field_fri   = [f.get("field_resonance_index", 0.0) for f in fields]
    field_dphi  = [f.get("delta_phi_field", 0.0) for f in fields]

    summary["fields"] = {
        "num_pages": safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field": safe_stats(field_dphi),
    }

    # Top selections
    summary["top_nodes_by_intensity"] = sorted(
        nodes,
        key=lambda n: float(n.get("intensity", 0.0)),
        reverse=True,
    )[:25]

    summary["top_nodes_by_gradient"] = sorted(
        nodes,
        key=lambda n: float(n.get("local_gradient", 0.0)),
        reverse=True,
    )[:25]

    summary["top_pages_by_harmonic_index"] = sorted(
        pages_lattice,
        key=lambda p: float(p.get("lattice_harmonic_index", 0.0)),
        reverse=True,
    )[:10]

    return summary

def ledger_record(summary):
    nodes = summary.get("nodes", {})
    edges = summary.get("edges", {})
    pages = summary.get("pages", {})
    fields = summary.get("fields", {})

    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_nodes": summary.get("num_nodes", 0),
        "num_edges": summary.get("num_edges", 0),
        "num_pages": summary.get("num_pages", 0),
        "num_fields": summary.get("num_fields", 0),
        "node_intensity_mean": nodes.get("intensity", {}).get("mean", 0.0),
        "node_degree_mean": nodes.get("degree", {}).get("mean", 0.0),
        "node_gradient_mean": nodes.get("local_gradient", {}).get("mean", 0.0),
        "edge_weight_mean": edges.get("weight_intensity", {}).get("mean", 0.0),
        "edge_phase_distance_mean": edges.get("phase_distance", {}).get("mean", 0.0),
        "page_harmonic_index_mean": pages.get("lattice_harmonic_index", {}).get("mean", 0.0),
        "field_spread_mean": fields.get("num_pages", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir   = os.path.join(root, "data")
    meaning_v6_1 = os.path.join(data_dir, "meaning_v6_1")
    meaning_v7_0 = os.path.join(data_dir, "meaning_v7_0")

    expansion_path   = os.path.join(meaning_v6_1, "hybrid_glyph_expansion_v6_1.json")
    out_lattice_path = os.path.join(meaning_v7_0, "hybrid_glyph_lattice_v7_0.json")
    out_summary_path = os.path.join(meaning_v7_0, "hybrid_glyph_lattice_summary_v7_0.json")
    out_ledger_path  = os.path.join(meaning_v7_0, "hybrid_glyph_lattice_ledger_v7_0.jsonl")

    expansion_obj = load_expansion(expansion_path)
    lattice_obj = build_lattice(expansion_obj)
    summary = summarize_lattice(lattice_obj)
    led = ledger_record(summary)

    save_json(out_lattice_path, lattice_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid glyph lattice v7.0       ->", out_lattice_path)
    print("Hybrid glyph lattice summary v7.0->", out_summary_path)
    print("Hybrid glyph lattice ledger v7.0 ->", out_ledger_path)

if __name__ == "__main__":
    main()
