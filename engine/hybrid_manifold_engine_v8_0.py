#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v8.0 — Hybrid Multimodal Manifold Engine (Glyph+Image → Bands)
# Auto-written by All-One PS (v8.0)

import os
import json
import math
import datetime
import hashlib

VERSION = "v8_0"

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
# Image seed signature (bytes-only)
# ─────────────────────────────

def load_image_signature(path):
    if not os.path.isfile(path):
        return {
            "exists": False,
            "path": path,
            "size_bytes": 0,
            "mtime_utc": None,
            "hash_sha256": None,
            "coupling_scalar": 0.5,
            "note": "File not found; neutral symbolic signature used.",
        }

    try:
        size_bytes = os.path.getsize(path)
        mtime      = os.path.getmtime(path)
        mtime_utc  = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc).isoformat()

        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        digest = h.hexdigest()

        # Map a small slice of the hash into (0,1) as a stable scalar
        # (purely numeric; no interpretation of visual content).
        try:
            sub = digest[:8]
            val = int(sub, 16)
            coupling_scalar = 0.3 + 0.4 * (val / float(0xFFFFFFFF))
        except Exception:
            coupling_scalar = 0.5

        return {
            "exists": True,
            "path": path,
            "size_bytes": int(size_bytes),
            "mtime_utc": mtime_utc,
            "hash_sha256": digest,
            "coupling_scalar": float(coupling_scalar),
            "note": "Derived from file bytes only; no visual decoding.",
        }
    except Exception:
        return {
            "exists": False,
            "path": path,
            "size_bytes": 0,
            "mtime_utc": None,
            "hash_sha256": None,
            "coupling_scalar": 0.5,
            "note": "Error reading file; neutral symbolic signature used.",
        }

# ─────────────────────────────
# Load v7.1 image lattice
# ─────────────────────────────

def build_stub_image_lattice():
    return {
        "version": "v7_1_stub",
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": {},
        "image_signature": {
            "exists": False,
            "path": "",
            "size_bytes": 0,
            "mtime_utc": None,
            "hash_sha256": None,
            "coupling_scalar": 0.5,
            "note": "stub",
        },
        "num_nodes": 0,
        "num_edges": 0,
        "nodes": [],
        "edges": [],
        "pages_lattice_image": [],
        "fields": [],
    }

def load_image_lattice(path):
    data = load_json(path, default=None)
    if not data or "nodes" not in data or "edges" not in data:
        data = build_stub_image_lattice()
    return data

# ─────────────────────────────
# Manifold construction
# ─────────────────────────────

def build_manifold(image_lattice_obj, image_sig):
    nodes    = image_lattice_obj.get("nodes", [])
    edges    = image_lattice_obj.get("edges", [])
    pages_im = image_lattice_obj.get("pages_lattice_image", [])
    fields   = image_lattice_obj.get("fields", [])
    glyph_seed_meta = image_lattice_obj.get("glyph_seed", {})

    coupling_scalar = float(image_sig.get("coupling_scalar", 0.5))

    # Extract basic scales
    intensities = [float(n.get("intensity", 0.0)) for n in nodes]
    if intensities:
        i_min = min(intensities)
        i_max = max(intensities)
        span  = max(i_max - i_min, 1e-9)
    else:
        i_min = 0.0
        span  = 1.0

    manifold_nodes = []
    manifold_pages = []

    # Per-page grouping
    page_to_nodes = {}
    for n in nodes:
        pid = str(n.get("page_id", "")) or "UNKNOWN_PAGE"
        page_to_nodes.setdefault(pid, []).append(n)

    # Node-level manifold coordinates
    for n in nodes:
        pid   = str(n.get("page_id", "")) or "UNKNOWN_PAGE"
        gid   = str(n.get("glyph_id", "")) or "UNKNOWN"
        t     = float(n.get("normalized_index", 0.0))  # [0,1)
        inten = float(n.get("intensity", 0.0))
        img_c = float(n.get("image_coupling", 0.0))

        inten_norm = (inten - i_min) / span
        inten_norm = max(0.0, min(1.0, inten_norm))

        # Manifold geometry:
        #   θ from normalized index (page position)
        #   r blends intensity + image_coupling, gated by external scalar
        theta = 2.0 * math.pi * t
        r_base = 1.0 + 0.75 * inten_norm
        r_img  = 0.5 * img_c * coupling_scalar
        r      = r_base + r_img

        x = r * math.cos(theta)
        y = r * math.sin(theta)

        # Band index encodes how "close" node is to joint intensity+image seed
        joint_score = 0.5 * inten_norm + 0.5 * img_c
        band_index = int(math.floor(10.0 * joint_score))
        if band_index < 0:
            band_index = 0
        if band_index > 9:
            band_index = 9

        if band_index <= 2:
            band_label = "low"
        elif band_index <= 6:
            band_label = "mid"
        else:
            band_label = "high"

        node_out = dict(n)
        node_out.update({
            "manifold_radius": float(r),
            "manifold_theta": float(theta),
            "manifold_x": float(x),
            "manifold_y": float(y),
            "manifold_band_index": int(band_index),
            "manifold_band_label": band_label,
            "image_coupling_scalar": coupling_scalar,
        })
        manifold_nodes.append(node_out)

    # Page-level coherence metrics
    for p in pages_im:
        pid = str(p.get("page_id", "")) or "UNKNOWN_PAGE"
        pnodes = page_to_nodes.get(pid, [])
        radii  = []

        for n in pnodes:
            t     = float(n.get("normalized_index", 0.0))
            inten = float(n.get("intensity", 0.0))
            img_c = float(n.get("image_coupling", 0.0))
            inten_norm = (inten - i_min) / span
            inten_norm = max(0.0, min(1.0, inten_norm))
            r_base = 1.0 + 0.75 * inten_norm
            r_img  = 0.5 * img_c * coupling_scalar
            r      = r_base + r_img
            radii.append(r)

        if radii:
            mean_r = sum(radii) / len(radii)
            var_r  = sum((ri - mean_r) ** 2 for ri in radii) / len(radii)
            # Coherence: higher when radii are similar (low variance)
            manifold_coherence = 1.0 / (1.0 + var_r)
        else:
            mean_r = 0.0
            var_r  = 0.0
            manifold_coherence = 0.0

        page_out = dict(p)
        page_out.update({
            "manifold_radius_mean": float(mean_r),
            "manifold_radius_var": float(var_r),
            "manifold_coherence": float(manifold_coherence),
        })
        manifold_pages.append(page_out)

    manifold_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "image_signature": image_sig,
        "num_nodes": len(manifold_nodes),
        "num_edges": len(edges),
        "nodes": manifold_nodes,
        "edges": edges,
        "pages_manifold": manifold_pages,
        "fields": fields,
    }
    return manifold_obj

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_manifold(manifold_obj):
    nodes = manifold_obj.get("nodes", [])
    pages = manifold_obj.get("pages_manifold", [])
    fields = manifold_obj.get("fields", [])
    edges = manifold_obj.get("edges", [])

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_nodes": manifold_obj.get("num_nodes", len(nodes)),
        "num_edges": manifold_obj.get("num_edges", len(edges)),
        "num_pages": len(pages),
        "num_fields": len(fields),
        "glyph_seed": manifold_obj.get("glyph_seed", {}),
        "image_signature": manifold_obj.get("image_signature", {}),
    }

    radii    = [n.get("manifold_radius", 0.0) for n in nodes]
    bands    = [n.get("manifold_band_index", 0) for n in nodes]
    img_c    = [n.get("image_coupling", 0.0) for n in nodes]
    degrees  = [n.get("degree", 0.0) for n in nodes]
    grad     = [n.get("local_gradient", 0.0) for n in nodes]

    summary["nodes"] = {
        "radius": safe_stats(radii),
        "band_index": safe_stats(bands),
        "image_coupling": safe_stats(img_c),
        "degree": safe_stats(degrees),
        "local_gradient": safe_stats(grad),
    }

    page_coh = [p.get("manifold_coherence", 0.0) for p in pages]
    summary["pages"] = {
        "manifold_coherence": safe_stats(page_coh),
    }

    field_pages = [f.get("num_pages", 0) for f in fields]
    field_fri   = [f.get("field_resonance_index", 0.0) for f in fields]
    field_dphi  = [f.get("delta_phi_field", 0.0) for f in fields]

    summary["fields"] = {
        "num_pages": safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field": safe_stats(field_dphi),
    }

    summary["top_nodes_by_radius"] = sorted(
        nodes,
        key=lambda n: float(n.get("manifold_radius", 0.0)),
        reverse=True,
    )[:25]

    summary["top_nodes_by_band_index"] = sorted(
        nodes,
        key=lambda n: float(n.get("manifold_band_index", 0)),
        reverse=True,
    )[:25]

    summary["top_pages_by_coherence"] = sorted(
        pages,
        key=lambda p: float(p.get("manifold_coherence", 0.0)),
        reverse=True,
    )[:10]

    return summary

def ledger_record(summary):
    nodes = summary.get("nodes", {})
    pages = summary.get("pages", {})
    fields = summary.get("fields", {})

    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_nodes": summary.get("num_nodes", 0),
        "num_edges": summary.get("num_edges", 0),
        "num_pages": summary.get("num_pages", 0),
        "num_fields": summary.get("num_fields", 0),
        "node_radius_mean": nodes.get("radius", {}).get("mean", 0.0),
        "node_band_index_mean": nodes.get("band_index", {}).get("mean", 0.0),
        "node_image_coupling_mean": nodes.get("image_coupling", {}).get("mean", 0.0),
        "page_manifold_coherence_mean": pages.get("manifold_coherence", {}).get("mean", 0.0),
        "field_spread_mean": fields.get("num_pages", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir   = os.path.join(root, "data")
    meaning_v7_1 = os.path.join(data_dir, "meaning_v7_1")
    meaning_v8_0 = os.path.join(data_dir, "meaning_v8_0")
    image_dir    = os.path.join(data_dir, "images")

    lattice_path = os.path.join(meaning_v7_1, "hybrid_image_lattice_v7_1.json")
    out_manifold_path = os.path.join(meaning_v8_0, "hybrid_manifold_v8_0.json")
    out_summary_path  = os.path.join(meaning_v8_0, "hybrid_manifold_summary_v8_0.json")
    out_ledger_path   = os.path.join(meaning_v8_0, "hybrid_manifold_ledger_v8_0.jsonl")

    image_seed_path = os.path.join(image_dir, "voynich_hybrid_seed_v8_0.png")

    image_lattice_obj = load_image_lattice(lattice_path)
    image_sig = load_image_signature(image_seed_path)

    manifold_obj = build_manifold(image_lattice_obj, image_sig)
    summary = summarize_manifold(manifold_obj)
    led = ledger_record(summary)

    save_json(out_manifold_path, manifold_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid manifold v8.0            ->", out_manifold_path)
    print("Hybrid manifold summary v8.0    ->", out_summary_path)
    print("Hybrid manifold ledger v8.0     ->", out_ledger_path)

if __name__ == "__main__":
    main()
