#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v8.1 — Hybrid Manifold Projection Engine
#   v8.0 manifold + v8.1 image seed → projection bands + coherence
# Expected image path (local): data/images/voynich_hybrid_seed_v8_1.png

import os
import json
import math
import datetime
import hashlib

VERSION = "v8_1"


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
# Image signature (file-only, no semantics)
# ─────────────────────────────

def compute_image_signature(image_path):
    """
    Use only file bytes + metadata as a neutral signature.
    No semantic/image decoding.
    """
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

    st = os.stat(image_path)
    size_bytes = int(st.st_size)
    mtime_utc = datetime.datetime.fromtimestamp(
        st.st_mtime, tz=datetime.timezone.utc
    ).isoformat()

    with open(image_path, "rb") as f:
        data = f.read()

    h = hashlib.sha256(data).hexdigest()
    # Map first 8 hex chars → [0.25, 0.75] band
    first8 = int(h[:8], 16)
    denom = float(0xFFFFFFFF) if 0xFFFFFFFF != 0 else 1.0
    norm = float(first8) / denom
    coupling_scalar = float(0.25 + 0.5 * norm)

    sig.update(
        {
            "exists": True,
            "size_bytes": size_bytes,
            "mtime_utc": mtime_utc,
            "hash_sha256": h,
            "coupling_scalar": coupling_scalar,
            "note": "File exists; signature from bytes only (no semantic decoding).",
        }
    )
    return sig


# ─────────────────────────────
# Manifold → Projection
# ─────────────────────────────

def project_manifold(manifold_obj, image_sig):
    nodes_in = manifold_obj.get("nodes", []) or []
    edges = manifold_obj.get("edges", []) or []
    pages_in = manifold_obj.get("pages_manifold", manifold_obj.get("pages", [])) or []
    fields = manifold_obj.get("fields", []) or []

    scalar = image_sig.get("coupling_scalar", 0.5)
    try:
        scalar = float(scalar)
    except Exception:
        scalar = 0.5

    # Clamp for safety
    if scalar < 0.0:
        scalar = 0.0
    if scalar > 1.0:
        scalar = 1.0

    projected_nodes = []

    for n in nodes_in:
        node = dict(n)

        radius = float(node.get("manifold_radius", 0.0))
        band_index = float(node.get("manifold_band_index", 0.0))
        image_coupling = float(node.get("image_coupling", 0.0))

        # Projection scaling: manifold radius × (image_coupling × global scalar)
        base_scale = 0.75 + 0.5 * image_coupling * scalar
        projected_radius = radius * base_scale

        projected_band_index = band_index * (0.5 + scalar)
        if projected_band_index < 0.0:
            projected_band_index = 0.0
        if projected_band_index > 8.0:
            projected_band_index = 8.0

        if projected_band_index >= 6.0:
            band_label = "high"
        elif projected_band_index >= 2.5:
            band_label = "mid"
        else:
            band_label = "low"

        # Projection coherence: how close projected radius stays to original
        projection_coherence = 1.0 / (1.0 + abs(projected_radius - radius))

        node["projection_radius"] = float(projected_radius)
        node["projection_band_index"] = float(projected_band_index)
        node["projection_band_label"] = band_label
        node["projection_coherence"] = float(projection_coherence)

        projected_nodes.append(node)

    # Page-level projection metrics
    page_to_nodes = {}
    for n in projected_nodes:
        pid = str(n.get("page_id", "")) or "GLOBAL_PAGE"
        page_to_nodes.setdefault(pid, []).append(n)

    pages_projection = []
    for p in pages_in:
        pid = str(p.get("page_id", "")) or "GLOBAL_PAGE"
        pnodes = page_to_nodes.get(pid, [])
        radii = [float(n.get("projection_radius", 0.0)) for n in pnodes]
        if radii:
            mean_r = sum(radii) / len(radii)
            var_r = sum((r - mean_r) ** 2 for r in radii) / len(radii)
            coherence = 1.0 / (1.0 + var_r)
        else:
            mean_r = 0.0
            var_r = 0.0
            coherence = 0.0

        page_out = dict(p)
        page_out["projection_radius_mean"] = float(mean_r)
        page_out["projection_radius_var"] = float(var_r)
        page_out["projection_coherence"] = float(coherence)
        pages_projection.append(page_out)

    projection_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": manifold_obj.get("glyph_seed", {}),
        "image_signature": image_sig,
        "num_nodes": len(projected_nodes),
        "num_edges": len(edges),
        "nodes": projected_nodes,
        "edges": edges,
        "pages_manifold": pages_in,
        "pages_projection": pages_projection,
        "fields": fields,
    }
    return projection_obj


# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_projection(proj_obj):
    nodes = proj_obj.get("nodes", []) or []
    edges = proj_obj.get("edges", []) or []
    pages_proj = proj_obj.get("pages_projection", []) or []
    fields = proj_obj.get("fields", []) or []

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_nodes": proj_obj.get("num_nodes", len(nodes)),
        "num_edges": proj_obj.get("num_edges", len(edges)),
        "num_pages": len(pages_proj),
        "num_fields": len(fields),
        "glyph_seed": proj_obj.get("glyph_seed", {}),
        "image_signature": proj_obj.get("image_signature", {}),
    }

    proj_radii = [n.get("projection_radius", 0.0) for n in nodes]
    proj_bands = [n.get("projection_band_index", 0.0) for n in nodes]
    img_coupling = [n.get("image_coupling", 0.0) for n in nodes]
    degrees = [n.get("degree", 0.0) for n in nodes]
    gradients = [n.get("local_gradient", 0.0) for n in nodes]

    summary["nodes"] = {
        "projection_radius": safe_stats(proj_radii),
        "projection_band_index": safe_stats(proj_bands),
        "image_coupling": safe_stats(img_coupling),
        "degree": safe_stats(degrees),
        "local_gradient": safe_stats(gradients),
    }

    proj_coh = [p.get("projection_coherence", 0.0) for p in pages_proj]
    summary["pages"] = {
        "projection_coherence": safe_stats(proj_coh),
    }

    field_pages = [f.get("num_pages", 0) for f in fields]
    field_fri = [f.get("field_resonance_index", 0.0) for f in fields]
    field_dphi = [f.get("delta_phi_field", 0.0) for f in fields]
    summary["fields"] = {
        "num_pages": safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field": safe_stats(field_dphi),
    }

    # Collections for "top" views
    summary["top_nodes_by_projection_radius"] = sorted(
        nodes,
        key=lambda n: float(n.get("projection_radius", 0.0)),
        reverse=True,
    )[:25]

    summary["top_nodes_by_projection_band"] = sorted(
        nodes,
        key=lambda n: float(n.get("projection_band_index", 0.0)),
        reverse=True,
    )[:25]

    summary["top_pages_by_projection_coherence"] = sorted(
        pages_proj,
        key=lambda p: float(p.get("projection_coherence", 0.0)),
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
        "node_projection_radius_mean": nodes.get("projection_radius", {}).get("mean", 0.0),
        "node_projection_band_index_mean": nodes.get("projection_band_index", {}).get("mean", 0.0),
        "node_image_coupling_mean": nodes.get("image_coupling", {}).get("mean", 0.0),
        "page_projection_coherence_mean": pages.get("projection_coherence", {}).get("mean", 0.0),
        "field_spread_mean": fields.get("num_pages", {}).get("mean", 0.0),
    }


# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir = os.path.join(root, "data")
    meaning_v8_0 = os.path.join(data_dir, "meaning_v8_0")
    meaning_v8_1 = os.path.join(data_dir, "meaning_v8_1")
    images_dir = os.path.join(data_dir, "images")

    manifold_path = os.path.join(meaning_v8_0, "hybrid_manifold_v8_0.json")
    out_proj_path = os.path.join(meaning_v8_1, "hybrid_manifold_projection_v8_1.json")
    out_summary_path = os.path.join(meaning_v8_1, "hybrid_manifold_projection_summary_v8_1.json")
    out_ledger_path = os.path.join(meaning_v8_1, "hybrid_manifold_projection_ledger_v8_1.jsonl")

    image_path = os.path.join(images_dir, "voynich_hybrid_seed_v8_1.png")

    manifold_obj = load_json(manifold_path, default={"nodes": [], "edges": [], "fields": []})
    if manifold_obj is None:
        manifold_obj = {"nodes": [], "edges": [], "fields": []}

    image_sig = compute_image_signature(image_path)
    proj_obj = project_manifold(manifold_obj, image_sig)
    summary = summarize_projection(proj_obj)
    led = ledger_record(summary)

    save_json(out_proj_path, proj_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid manifold projection v8.1   ->", out_proj_path)
    print("Hybrid manifold proj summary v8.1->", out_summary_path)
    print("Hybrid manifold proj ledger v8.1 ->", out_ledger_path)


if __name__ == "__main__":
    main()
