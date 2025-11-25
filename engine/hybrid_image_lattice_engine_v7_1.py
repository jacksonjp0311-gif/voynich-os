#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v7.1 — Hybrid Image-Lattice Coupling Engine
# Auto-written by All-One PS (v7.1)

import os
import json
import math
import datetime
import hashlib

VERSION = "v7_1"

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
# Lattice helpers (from v7.0)
# ─────────────────────────────

def build_stub_lattice():
    # Minimal stub compatible with v7.0 structure
    return {
        "version": "v7_0_stub",
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": {},
        "num_nodes": 0,
        "num_edges": 0,
        "nodes": [],
        "edges": [],
        "pages_lattice": [],
        "fields": [],
    }

def load_lattice(path):
    data = load_json(path, default=None)
    if not data or "nodes" not in data or "edges" not in data:
        data = build_stub_lattice()
    return data

# ─────────────────────────────
# Image signature (file-level only)
# ─────────────────────────────

def compute_image_signature(image_path):
    sig = {
        "exists": False,
        "path": image_path,
        "size_bytes": 0,
        "mtime_utc": None,
        "hash_sha256": None,
        "coupling_scalar": 0.5,
        "note": "If exists, derived from file bytes only; used as neutral symbolic signature.",
    }

    if not os.path.isfile(image_path):
        return sig

    try:
        size = os.path.getsize(image_path)
        mtime = datetime.datetime.fromtimestamp(
            os.path.getmtime(image_path),
            tz=datetime.timezone.utc
        ).isoformat()

        h = hashlib.sha256()
        with open(image_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                if not chunk:
                    break
                h.update(chunk)
        digest = h.hexdigest()

        # Map last 8 hex chars into [0,1] scalar for global coupling
        tail = digest[-8:]
        tail_int = int(tail, 16)
        max_val = float(16**8 - 1)
        scalar = tail_int / max_val if max_val > 0 else 0.5

        sig["exists"] = True
        sig["size_bytes"] = int(size)
        sig["mtime_utc"] = mtime
        sig["hash_sha256"] = digest
        sig["coupling_scalar"] = float(scalar)
        sig["note"] = "File-bytes signature only; used as global image-lattice coupling scalar."
        return sig
    except Exception as e:
        sig["note"] = "Signature fallback due to error: {0}".format(e)
        return sig

# ─────────────────────────────
# Image-lattice coupling
# ─────────────────────────────

def build_image_lattice(lattice_obj, image_sig):
    nodes_in = lattice_obj.get("nodes", []) or []
    edges_in = lattice_obj.get("edges", []) or []
    pages_lattice = lattice_obj.get("pages_lattice", []) or []
    fields = lattice_obj.get("fields", []) or []
    glyph_seed_meta = lattice_obj.get("glyph_seed", {}) or {}

    # Copy nodes/edges so we don't mutate the original object
    nodes = [dict(n) for n in nodes_in]
    edges = [dict(e) for e in edges_in]

    intensities = [float(n.get("intensity", 0.0)) for n in nodes]
    if intensities:
        imax = max(intensities)
    else:
        imax = 0.0

    global_scalar = float(image_sig.get("coupling_scalar", 0.5))

    # Node-level image coupling
    for node in nodes:
        base_intensity = float(node.get("intensity", 0.0))
        if imax > 0.0:
            norm = base_intensity / imax
        else:
            norm = 0.0

        # Simple harmonic blend: local intensity × global scalar
        coupling = norm * (0.5 + 0.5 * global_scalar)
        node["image_coupling"] = float(coupling)

        if coupling < 0.33:
            band = "low"
        elif coupling < 0.66:
            band = "mid"
        else:
            band = "high"
        node["image_band"] = band

    # Edge-level coupling (mean of node couplings)
    node_by_id = {n.get("glyph_id"): n for n in nodes if n.get("glyph_id") is not None}

    for edge in edges:
        ga = edge.get("glyph_a")
        gb = edge.get("glyph_b")
        ca = float(node_by_id.get(ga, {}).get("image_coupling", 0.0))
        cb = float(node_by_id.get(gb, {}).get("image_coupling", 0.0))
        edge["image_coupling_mean"] = float(0.5 * (ca + cb))

    # Page-level mean coupling
    pages_lattice_image = []
    for p in pages_lattice:
        pid = str(p.get("page_id", "")) or "UNKNOWN_PAGE"
        page_nodes = [n for n in nodes if str(n.get("page_id", "")) == pid]
        vals = [float(n.get("image_coupling", 0.0)) for n in page_nodes]
        if vals:
            mean_coupling = float(sum(vals) / len(vals))
        else:
            mean_coupling = 0.0
        rec = dict(p)
        rec["image_coupling_mean"] = mean_coupling
        pages_lattice_image.append(rec)

    image_lattice = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "image_signature": image_sig,
        "num_nodes": len(nodes),
        "num_edges": len(edges),
        "nodes": nodes,
        "edges": edges,
        "pages_lattice_image": pages_lattice_image,
        "fields": fields,
    }
    return image_lattice

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_image_lattice(image_lattice):
    nodes = image_lattice.get("nodes", []) or []
    edges = image_lattice.get("edges", []) or []
    pages_lattice_image = image_lattice.get("pages_lattice_image", []) or []
    fields = image_lattice.get("fields", []) or []

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_nodes": image_lattice.get("num_nodes", len(nodes)),
        "num_edges": image_lattice.get("num_edges", len(edges)),
        "num_pages": len(pages_lattice_image),
        "num_fields": len(fields),
        "glyph_seed": image_lattice.get("glyph_seed", {}),
        "image_signature": image_lattice.get("image_signature", {}),
    }

    intensities      = [float(n.get("intensity", 0.0)) for n in nodes] if nodes else []
    degrees          = [float(n.get("degree", 0.0)) for n in nodes] if nodes else []
    gradients        = [float(n.get("local_gradient", 0.0)) for n in nodes] if nodes else []
    image_couplings  = [float(n.get("image_coupling", 0.0)) for n in nodes] if nodes else []

    edge_weights     = [float(e.get("weight_intensity", 0.0)) for e in edges] if edges else []
    edge_phase       = [float(e.get("phase_distance", 0.0)) for e in edges] if edges else []
    edge_img_couple  = [float(e.get("image_coupling_mean", 0.0)) for e in edges] if edges else []

    page_image_coup  = [float(p.get("image_coupling_mean", 0.0)) for p in pages_lattice_image] if pages_lattice_image else []

    summary["nodes"] = {
        "intensity": safe_stats(intensities),
        "degree": safe_stats(degrees),
        "local_gradient": safe_stats(gradients),
        "image_coupling": safe_stats(image_couplings),
    }

    summary["edges"] = {
        "weight_intensity": safe_stats(edge_weights),
        "phase_distance": safe_stats(edge_phase),
        "image_coupling_mean": safe_stats(edge_img_couple),
    }

    summary["pages"] = {
        "image_coupling_mean": safe_stats(page_image_coup),
    }

    field_pages = [f.get("num_pages", 0) for f in fields]
    field_fri   = [f.get("field_resonance_index", 0.0) for f in fields]
    field_dphi  = [f.get("delta_phi_field", 0.0) for f in fields]

    summary["fields"] = {
        "num_pages": safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field": safe_stats(field_dphi),
    }

    summary["top_nodes_by_image_coupling"] = sorted(
        nodes,
        key=lambda n: float(n.get("image_coupling", 0.0)),
        reverse=True,
    )[:25]

    summary["top_edges_by_image_coupling"] = sorted(
        edges,
        key=lambda e: float(e.get("image_coupling_mean", 0.0)),
        reverse=True,
    )[:25]

    summary["top_pages_by_image_coupling"] = sorted(
        pages_lattice_image,
        key=lambda p: float(p.get("image_coupling_mean", 0.0)),
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
        "node_image_coupling_mean": nodes.get("image_coupling", {}).get("mean", 0.0),
        "edge_weight_mean": edges.get("weight_intensity", {}).get("mean", 0.0),
        "edge_phase_distance_mean": edges.get("phase_distance", {}).get("mean", 0.0),
        "edge_image_coupling_mean": edges.get("image_coupling_mean", {}).get("mean", 0.0),
        "page_image_coupling_mean": pages.get("image_coupling_mean", {}).get("mean", 0.0),
        "field_spread_mean": fields.get("num_pages", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir    = os.path.join(root, "data")
    meaning_v7_0 = os.path.join(data_dir, "meaning_v7_0")
    meaning_v7_1 = os.path.join(data_dir, "meaning_v7_1")
    images_dir   = os.path.join(data_dir, "images")

    os.makedirs(meaning_v7_1, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    lattice_path = os.path.join(meaning_v7_0, "hybrid_glyph_lattice_v7_0.json")
    image_path   = os.path.join(images_dir, "voynich_hybrid_seed_v7_1.png")

    out_lattice_path = os.path.join(meaning_v7_1, "hybrid_image_lattice_v7_1.json")
    out_summary_path = os.path.join(meaning_v7_1, "hybrid_image_lattice_summary_v7_1.json")
    out_ledger_path  = os.path.join(meaning_v7_1, "hybrid_image_lattice_ledger_v7_1.jsonl")

    lattice_obj = load_lattice(lattice_path)
    image_sig   = compute_image_signature(image_path)

    image_lattice = build_image_lattice(lattice_obj, image_sig)
    summary = summarize_image_lattice(image_lattice)
    led = ledger_record(summary)

    save_json(out_lattice_path, image_lattice)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid image lattice v7.1       ->", out_lattice_path)
    print("Hybrid image lattice summary v7.1->", out_summary_path)
    print("Hybrid image lattice ledger v7.1 ->", out_ledger_path)

if __name__ == "__main__":
    main()
