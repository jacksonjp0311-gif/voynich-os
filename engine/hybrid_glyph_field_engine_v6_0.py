#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v6.0 — Hybrid Glyph Field Engine (Image × Glyph × Field)
# Auto-written by All-One PS (v6.0)

import os
import json
import datetime

VERSION = "v6_0"

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
# Core loaders
# ─────────────────────────────

def build_stub_graph():
    """Fallback when earlier stages are missing."""
    return {
        "version": "v6_0_stub",
        "timestamp_utc": now_utc_iso(),
        "pages": [
            {
                "page_id": "GLOBAL_PAGE",
                "num_sentences": 0,
                "num_fields": 1,
                "coverage_ratio": 0.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
            }
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

def load_manuscript_graph(path):
    data = load_json(path, default=None)
    if not data or "pages" not in data or "fields" not in data:
        data = build_stub_graph()
    return data

def load_force_field(path):
    data = load_json(path, default=None)
    if not data or "pages" not in data or "fields" not in data:
        return {"pages": [], "fields": []}
    return data

def load_hybrid_graph(path):
    data = load_json(path, default=None)
    if not data or "pages" not in data or "fields" not in data:
        return {"pages": [], "fields": [], "glyph_seed": {}}
    return data

# ─────────────────────────────
# Hybrid glyph field construction
# ─────────────────────────────

def index_by_page_id(pages, key_name="page_id"):
    idx = {}
    for p in pages:
        pid = str(p.get(key_name, ""))
        if pid:
            idx[pid] = p
    return idx

def build_hybrid_glyph_field(manuscript_graph, force_field, hybrid_graph, glyph_seed_meta):
    """
    Fuse:
      • Manuscript geometry (v5.5)
      • Force-field geometry (v5.6)
      • Hybrid EVA/Takahashi stats (v5.5B)
    into a page-level glyph field descriptor.
    """

    mg_pages = manuscript_graph.get("pages", [])
    mg_fields = manuscript_graph.get("fields", [])

    ff_pages = force_field.get("pages", [])
    hg_pages = hybrid_graph.get("pages", [])
    hg_fields = hybrid_graph.get("fields", [])

    ff_index = index_by_page_id(ff_pages, "page_id")
    hg_index = index_by_page_id(hg_pages, "page_id")

    glyph_pages = []
    for mp in mg_pages:
        pid = str(mp.get("page_id", ""))

        # Manuscript metrics
        m_num_sent   = int(mp.get("num_sentences", 0))
        m_num_fields = int(mp.get("num_fields", 0))
        m_cov        = float(mp.get("coverage_ratio", 0.0))
        m_coh        = float(mp.get("coherence_index", 0.0))
        m_dphi       = float(mp.get("delta_phi_mean", 0.0))

        # Force-field metrics (neighbors, potential)
        ff = ff_index.get(pid, {})
        ff_deg        = int(ff.get("num_neighbors", 0))
        ff_force      = float(ff.get("force_potential", 0.0))
        ff_num_fields = int(ff.get("num_fields", m_num_fields))

        # Hybrid EVA/Taka stats
        hg = hg_index.get(pid, {})
        eva_tokens   = int(hg.get("hybrid_eva_tokens", 0))
        taka_tokens  = int(hg.get("hybrid_taka_tokens", 0))
        delta_tokens = int(hg.get("hybrid_delta_tokens", 0))
        edge_degree  = int(hg.get("edge_degree", 0))

        # Codex-style glyph field: combine structure, force, and hybrid tokens.
        # Intuition:
        #   glyph_grid_score ~ coverage * (1 + log(1 + fields)) * (1 + log(1 + degree))
        #   hybrid_intensity ~ (eva + taka) weighted by coherence
        #   field_resonance_mean ~ from field stats later, referenced per page by num_fields
        import math

        cov_term    = max(m_cov, 0.0)
        field_term  = math.log(1.0 + float(max(m_num_fields, 0)))
        degree_term = math.log(1.0 + float(max(ff_deg, edge_degree, 0)))

        glyph_grid_score = cov_term * (1.0 + field_term) * (1.0 + degree_term)

        total_tokens = float(max(eva_tokens + taka_tokens, 0))
        hybrid_intensity = m_coh * total_tokens

        glyph_pages.append({
            "page_id": pid,
            "num_sentences": m_num_sent,
            "num_fields": m_num_fields,
            "coverage_ratio": m_cov,
            "coherence_index": m_coh,
            "delta_phi_mean": m_dphi,

            "force_field_neighbors": ff_deg,
            "force_field_potential": ff_force,
            "force_field_fields": ff_num_fields,

            "hybrid_eva_tokens": eva_tokens,
            "hybrid_takahashi_tokens": taka_tokens,
            "hybrid_delta_tokens": delta_tokens,
            "hybrid_edge_degree": edge_degree,

            "glyph_grid_score": float(glyph_grid_score),
            "hybrid_intensity": float(hybrid_intensity),
        })

    # Field-level view: we just pass manuscript fields through with a minimal normalization.
    glyph_fields = []
    for f in mg_fields:
        glyph_fields.append({
            "field_id": str(f.get("field_id", "")),
            "num_pages": int(f.get("num_pages", 0)),
            "page_ids": [str(pid) for pid in f.get("page_ids", [])],
            "delta_phi_field": float(f.get("delta_phi_field", 0.0)),
            "field_resonance_index": float(f.get("field_resonance_index", 0.0)),
        })

    glyph_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "pages": glyph_pages,
        "fields": glyph_fields,
    }
    return glyph_obj

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_glyph_field(glyph_obj):
    pages = glyph_obj.get("pages", [])
    fields = glyph_obj.get("fields", [])

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": len(pages),
        "num_fields": len(fields),
        "glyph_seed": glyph_obj.get("glyph_seed", {}),
    }

    # Page metrics
    coh   = [p["coherence_index"] for p in pages]
    dphi  = [p["delta_phi_mean"] for p in pages]
    cov   = [p["coverage_ratio"] for p in pages]
    force = [p["force_field_potential"] for p in pages]
    deg   = [p["force_field_neighbors"] for p in pages]
    eva_t = [p["hybrid_eva_tokens"] for p in pages]
    tak_t = [p["hybrid_takahashi_tokens"] for p in pages]
    del_t = [p["hybrid_delta_tokens"] for p in pages]
    grid  = [p["glyph_grid_score"] for p in pages]
    hint  = [p["hybrid_intensity"] for p in pages]

    summary["pages"] = {
        "coherence_index":      safe_stats(coh),
        "delta_phi_mean":       safe_stats(dphi),
        "coverage_ratio":       safe_stats(cov),
        "force_potential":      safe_stats(force),
        "neighbor_degree":      safe_stats(deg),
        "eva_tokens":           safe_stats(eva_t),
        "takahashi_tokens":     safe_stats(tak_t),
        "delta_tokens":         safe_stats(del_t),
        "glyph_grid_score":     safe_stats(grid),
        "hybrid_intensity":     safe_stats(hint),
    }

    # Field metrics
    field_pages = [f["num_pages"] for f in fields]
    field_fri   = [f["field_resonance_index"] for f in fields]
    field_dphi  = [f["delta_phi_field"] for f in fields]

    summary["fields"] = {
        "num_pages":             safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field":       safe_stats(field_dphi),
    }

    # Top selections
    summary["top_pages_by_glyph_grid"] = sorted(
        pages,
        key=lambda p: float(p.get("glyph_grid_score", 0.0)),
        reverse=True,
    )[:10]

    summary["top_pages_by_hybrid_intensity"] = sorted(
        pages,
        key=lambda p: float(p.get("hybrid_intensity", 0.0)),
        reverse=True,
    )[:10]

    summary["top_fields_by_spread"] = sorted(
        fields,
        key=lambda f: int(f.get("num_pages", 0)),
        reverse=True,
    )[:10]

    return summary

def ledger_record(summary):
    pages = summary.get("pages", {})
    fields = summary.get("fields", {})
    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_pages": summary.get("num_pages", 0),
        "num_fields": summary.get("num_fields", 0),
        "glyph_grid_mean":    pages.get("glyph_grid_score", {}).get("mean", 0.0),
        "hybrid_intensity_mean": pages.get("hybrid_intensity", {}).get("mean", 0.0),
        "page_coherence_mean":   pages.get("coherence_index", {}).get("mean", 0.0),
        "page_force_mean":       pages.get("force_potential", {}).get("mean", 0.0),
        "field_spread_mean":     fields.get("num_pages", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir   = os.path.join(root, "data")
    meaning_v5_5 = os.path.join(data_dir, "meaning_v5_5")
    meaning_v5_6 = os.path.join(data_dir, "meaning_v5_6")
    meaning_v6_0 = os.path.join(data_dir, "meaning_v6_0")

    mg_path  = os.path.join(meaning_v5_5, "manuscript_graph_v5_5.json")
    ff_path  = os.path.join(meaning_v5_6, "manuscript_force_field_v5_6.json")
    hg_path  = os.path.join(meaning_v5_5, "hybrid_manuscript_graph_v5_5b.json")

    out_glyph_path   = os.path.join(meaning_v6_0, "hybrid_glyph_field_v6_0.json")
    out_summary_path = os.path.join(meaning_v6_0, "hybrid_glyph_field_summary_v6_0.json")
    out_ledger_path  = os.path.join(meaning_v6_0, "hybrid_glyph_field_ledger_v6_0.jsonl")

    manuscript_graph = load_manuscript_graph(mg_path)
    force_field      = load_force_field(ff_path)
    hybrid_graph     = load_hybrid_graph(hg_path)

    # Glyph seed: external image used only as symbolic signature, not as numeric input.
    glyph_seed_meta = {
        "mode": "external_image_signature",
        "tag": "voynich_hybrid_seed_v6_0",
        "note": "External image used as glyph seed only; no direct influence on token metrics.",
    }

    glyph_obj = build_hybrid_glyph_field(
        manuscript_graph,
        force_field,
        hybrid_graph,
        glyph_seed_meta,
    )

    summary = summarize_glyph_field(glyph_obj)
    led = ledger_record(summary)

    save_json(out_glyph_path, glyph_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid glyph field v6.0        ->", out_glyph_path)
    print("Hybrid glyph summary v6.0      ->", out_summary_path)
    print("Hybrid glyph ledger v6.0       ->", out_ledger_path)

if __name__ == "__main__":
    main()
