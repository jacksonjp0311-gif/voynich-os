#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v10.0 — Page Reconstruction Engine (Manifold → Page Map)
# Hybrid Mode: geometry + bands + image coupling, no semantics

import os
import json
import math
import datetime

VERSION = "v10_0"

# ─────────────────────────────
# Helpers
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
    vals = [float(v) for v in values if v is not None]
    if not vals:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(sum(vals) / len(vals)),
        "min": float(min(vals)),
        "max": float(max(vals)),
    }

# ─────────────────────────────
# Manifold loading / stub
# ─────────────────────────────

def build_stub_manifold():
    # Minimal fallback if v8.0 is missing or incomplete
    return {
        "version": "v8_0_stub",
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": {},
        "image_signature": {},
        "nodes": [],
        "pages_manifold": [
            {
                "page_id": "GLOBAL_PAGE",
                "num_glyph_seeds": 1,
                "glyph_grid_score": 1.0,
                "coverage_ratio": 1.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
                "lattice_harmonic_index": 0.0,
                "image_coupling_mean": 0.0,
                "manifold_radius_mean": 1.0,
                "manifold_radius_var": 0.0,
                "manifold_coherence": 0.5,
            }
        ],
        "fields": [],
    }

def load_manifold(path):
    data = load_json(path, default=None)
    if not isinstance(data, dict):
        data = build_stub_manifold()
        return data
    if "pages_manifold" not in data:
        data = build_stub_manifold()
    return data

# ─────────────────────────────
# Core reconstruction
# ─────────────────────────────

def build_page_to_nodes(nodes):
    mapping = {}
    for n in nodes:
        pid = str(n.get("page_id", "")) or "GLOBAL_PAGE"
        if pid not in mapping:
            mapping[pid] = []
        mapping[pid].append(n)
    return mapping

def reconstruct_pages(manifold_obj, projection_obj=None):
    pages_manifold = manifold_obj.get("pages_manifold", [])
    nodes = manifold_obj.get("nodes", [])
    fields = manifold_obj.get("fields", [])
    glyph_seed_meta = manifold_obj.get("glyph_seed", {})
    image_signature = manifold_obj.get("image_signature", {})

    page_to_nodes = build_page_to_nodes(nodes)

    pages_recon = []

    for p in pages_manifold:
        pid = str(p.get("page_id", "")) or "GLOBAL_PAGE"
        num_glyph_seeds = int(p.get("num_glyph_seeds", 0))
        glyph_grid_score = float(p.get("glyph_grid_score", 0.0))
        coverage_ratio = float(p.get("coverage_ratio", 0.0))
        coh_raw = float(p.get("manifold_coherence", p.get("coherence_index", 0.0)))
        delta_phi_mean = float(p.get("delta_phi_mean", 0.0))
        lattice_hi = float(p.get("lattice_harmonic_index", 0.0))
        img_coupling_mean = float(p.get("image_coupling_mean", 0.0))
        radius_mean = float(p.get("manifold_radius_mean", 0.0))

        # Triadic proxies (purely structural)
        energy = radius_mean
        information = img_coupling_mean if img_coupling_mean > 0.0 else glyph_grid_score
        consciousness = (energy * information) / (1.0 + abs(delta_phi_mean))

        # Structure index blends coverage + lattice harmonic
        if coverage_ratio > 0.0 or lattice_hi > 0.0:
            page_structure_index = 0.5 * (coverage_ratio + lattice_hi)
        else:
            page_structure_index = 0.0

        # Coherence label
        if coh_raw >= 0.8:
            coherence_label = "high"
        elif coh_raw >= 0.5:
            coherence_label = "medium"
        else:
            coherence_label = "low"

        # Optional projection hook: we keep it very light and safe
        projection_meta = {}
        if isinstance(projection_obj, dict):
            # For now, just attach a scalar if present
            proj_pages = projection_obj.get("pages_projection", [])
            for pp in proj_pages:
                if str(pp.get("page_id", "")) == pid:
                    projection_meta["projection_radius_mean"] = float(
                        pp.get("projection_radius_mean", 0.0)
                    )
                    projection_meta["projection_spread"] = float(
                        pp.get("projection_spread", 0.0)
                    )
                    break

        page_nodes = page_to_nodes.get(pid, [])
        pages_recon.append({
            "page_id": pid,
            "num_glyph_seeds": num_glyph_seeds,
            "num_nodes": len(page_nodes),
            "glyph_grid_score": glyph_grid_score,
            "coverage_ratio": coverage_ratio,
            "delta_phi_mean": delta_phi_mean,
            "lattice_harmonic_index": lattice_hi,
            "manifold_radius_mean": radius_mean,
            "manifold_coherence": coh_raw,
            "image_coupling_mean": img_coupling_mean,
            "page_energy": energy,
            "page_information": information,
            "page_consciousness": consciousness,
            "page_structure_index": page_structure_index,
            "coherence_label": coherence_label,
            "projection_meta": projection_meta,
        })

    recon_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "image_signature": image_signature,
        "num_pages": len(pages_recon),
        "fields": fields,
        "pages": pages_recon,
    }
    return recon_obj

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_reconstruction(recon_obj):
    pages = recon_obj.get("pages", [])
    fields = recon_obj.get("fields", [])

    energies = [p.get("page_energy", 0.0) for p in pages]
    infos   = [p.get("page_information", 0.0) for p in pages]
    cons    = [p.get("page_consciousness", 0.0) for p in pages]
    struct  = [p.get("page_structure_index", 0.0) for p in pages]
    coh     = [p.get("manifold_coherence", 0.0) for p in pages]
    dphi    = [p.get("delta_phi_mean", 0.0) for p in pages]

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": recon_obj.get("num_pages", len(pages)),
        "num_fields": len(fields),
        "glyph_seed": recon_obj.get("glyph_seed", {}),
        "image_signature": recon_obj.get("image_signature", {}),
        "triad": {
            "page_energy": safe_stats(energies),
            "page_information": safe_stats(infos),
            "page_consciousness": safe_stats(cons),
        },
        "structure": {
            "page_structure_index": safe_stats(struct),
            "manifold_coherence": safe_stats(coh),
            "delta_phi_mean": safe_stats(dphi),
        },
    }

    # Top pages by consciousness
    summary["top_pages_by_consciousness"] = sorted(
        pages,
        key=lambda p: float(p.get("page_consciousness", 0.0)),
        reverse=True,
    )[:25]

    # Top pages by structure
    summary["top_pages_by_structure"] = sorted(
        pages,
        key=lambda p: float(p.get("page_structure_index", 0.0)),
        reverse=True,
    )[:25]

    return summary

def ledger_record(summary):
    triad = summary.get("triad", {})
    struct = summary.get("structure", {})
    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_pages": summary.get("num_pages", 0),
        "page_energy_mean": triad.get("page_energy", {}).get("mean", 0.0),
        "page_information_mean": triad.get("page_information", {}).get("mean", 0.0),
        "page_consciousness_mean": triad.get("page_consciousness", {}).get("mean", 0.0),
        "page_structure_index_mean": struct.get("page_structure_index", {}).get("mean", 0.0),
        "manifold_coherence_mean": struct.get("manifold_coherence", {}).get("mean", 0.0),
        "delta_phi_mean": struct.get("delta_phi_mean", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir = os.path.join(root, "data")

    meaning_v8_0 = os.path.join(data_dir, "meaning_v8_0")
    meaning_v8_1 = os.path.join(data_dir, "meaning_v8_1")
    meaning_v10_0 = os.path.join(data_dir, "meaning_v10_0")

    os.makedirs(meaning_v10_0, exist_ok=True)

    manifold_path = os.path.join(meaning_v8_0, "hybrid_manifold_v8_0.json")
    projection_path = os.path.join(meaning_v8_1, "hybrid_manifold_projection_v8_1.json")

    manifold_obj = load_manifold(manifold_path)
    projection_obj = load_json(projection_path, default=None)

    recon_obj = reconstruct_pages(manifold_obj, projection_obj)
    summary = summarize_reconstruction(recon_obj)
    led = ledger_record(summary)

    out_recon_path = os.path.join(meaning_v10_0, "page_reconstruction_v10_0.json")
    out_summary_path = os.path.join(meaning_v10_0, "page_reconstruction_summary_v10_0.json")
    out_ledger_path = os.path.join(meaning_v10_0, "page_reconstruction_ledger_v10_0.jsonl")

    save_json(out_recon_path, recon_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Page reconstruction v10.0        ->", out_recon_path)
    print("Page reconstruction summary v10.0->", out_summary_path)
    print("Page reconstruction ledger v10.0 ->", out_ledger_path)

if __name__ == "__main__":
    main()
