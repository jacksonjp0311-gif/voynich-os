#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v5.5B — Hybrid Manuscript Graph Engine
# Auto-written by All-One PS (v5.5B)

import os
import json
import datetime

VERSION = "v5_5b"

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
# Loading core layers
# ─────────────────────────────

def build_stub_graph():
    """Fallback when manuscript graph is missing."""
    return {
        "version": "v5_5_stub",
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
        "edges": [
            {"page_id": "GLOBAL_PAGE", "field_id": "meta"}
        ],
    }

def load_manuscript_graph(path):
    data = load_json(path, default=None)
    if not data or "pages" not in data or "fields" not in data:
        data = build_stub_graph()
    pages = data.get("pages", [])
    fields = data.get("fields", [])
    edges = data.get("edges", [])
    return pages, fields, edges

def load_hybrid_corpus(path):
    data = load_json(path, default=None)
    if not data:
        return {"pages": [], "sources": {}}
    pages = data.get("pages", [])
    sources = data.get("sources", {})
    return {"pages": pages, "sources": sources}

# ─────────────────────────────
# Hybrid graph construction
# ─────────────────────────────

def build_hybrid_graph(manuscript_pages, manuscript_fields, manuscript_edges,
                       hybrid_corpus):
    # Map hybrid per-page stats: page_id -> dict
    hybrid_page_map = {}
    for hp in hybrid_corpus.get("pages", []):
        pid = str(hp.get("page_id", ""))
        if not pid:
            continue
        eva = hp.get("eva", {}) or {}
        taka = hp.get("takahashi", {}) or {}
        hybrid_page_map[pid] = {
            "eva_lines": int(eva.get("num_lines", 0)),
            "eva_tokens": int(eva.get("num_tokens", 0)),
            "taka_lines": int(taka.get("num_lines", 0)),
            "taka_tokens": int(taka.get("num_tokens", 0)),
            "delta_lines": int(hp.get("delta_lines", 0)),
            "delta_tokens": int(hp.get("delta_tokens", 0)),
        }

    # Build quick degree map from edges
    page_degree = {}
    for e in manuscript_edges:
        pid = str(e.get("page_id", ""))
        if not pid:
            continue
        page_degree[pid] = page_degree.get(pid, 0) + 1

    # Hybrid pages: merge manuscript page metrics with hybrid EVA/Taka stats
    hybrid_pages = []
    for mp in manuscript_pages:
        pid = str(mp.get("page_id", ""))
        m_num_sent = int(mp.get("num_sentences", 0))
        m_num_fields = int(mp.get("num_fields", 0))
        m_cov = float(mp.get("coverage_ratio", 0.0))
        m_coh = float(mp.get("coherence_index", 0.0))
        m_dphi = float(mp.get("delta_phi_mean", 0.0))

        hp = hybrid_page_map.get(pid, {
            "eva_lines": 0,
            "eva_tokens": 0,
            "taka_lines": 0,
            "taka_tokens": 0,
            "delta_lines": 0,
            "delta_tokens": 0,
        })

        hybrid_pages.append({
            "page_id": pid,
            "num_sentences": m_num_sent,
            "num_fields": m_num_fields,
            "coverage_ratio": m_cov,
            "coherence_index": m_coh,
            "delta_phi_mean": m_dphi,
            "hybrid_eva_lines": hp["eva_lines"],
            "hybrid_eva_tokens": hp["eva_tokens"],
            "hybrid_taka_lines": hp["taka_lines"],
            "hybrid_taka_tokens": hp["taka_tokens"],
            "hybrid_delta_lines": hp["delta_lines"],
            "hybrid_delta_tokens": hp["delta_tokens"],
            "edge_degree": int(page_degree.get(pid, 0)),
        })

    # For v5.5B we pass manuscript_fields through unchanged
    hybrid_fields = []
    for f in manuscript_fields:
        hybrid_fields.append({
            "field_id": str(f.get("field_id", "")),
            "num_pages": int(f.get("num_pages", 0)),
            "page_ids": [str(pid) for pid in f.get("page_ids", [])],
            "delta_phi_field": float(f.get("delta_phi_field", 0.0)),
            "field_resonance_index": float(f.get("field_resonance_index", 0.0)),
        })

    return hybrid_pages, hybrid_fields

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_hybrid(hybrid_pages, hybrid_fields, glyph_seed_meta):
    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": len(hybrid_pages),
        "num_fields": len(hybrid_fields),
        "glyph_seed": glyph_seed_meta,
    }

    # Page-level stats
    coh   = [p["coherence_index"] for p in hybrid_pages]
    dphi  = [p["delta_phi_mean"] for p in hybrid_pages]
    cov   = [p["coverage_ratio"] for p in hybrid_pages]
    eva_t = [p["hybrid_eva_tokens"] for p in hybrid_pages]
    taka_t = [p["hybrid_taka_tokens"] for p in hybrid_pages]
    delta_t = [p["hybrid_delta_tokens"] for p in hybrid_pages]
    deg   = [p["edge_degree"] for p in hybrid_pages]

    summary["pages"] = {
        "coherence_index":    safe_stats(coh),
        "delta_phi_mean":     safe_stats(dphi),
        "coverage_ratio":     safe_stats(cov),
        "eva_tokens":         safe_stats(eva_t),
        "takahashi_tokens":   safe_stats(taka_t),
        "delta_tokens":       safe_stats(delta_t),
        "edge_degree":        safe_stats(deg),
    }

    # Field-level stats
    field_pages = [f["num_pages"] for f in hybrid_fields]
    field_fri   = [f["field_resonance_index"] for f in hybrid_fields]
    field_dphi  = [f["delta_phi_field"] for f in hybrid_fields]

    summary["fields"] = {
        "num_pages":             safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field":       safe_stats(field_dphi),
    }

    # Simple top lists
    summary["top_pages_by_eva_tokens"] = sorted(
        hybrid_pages,
        key=lambda p: float(p.get("hybrid_eva_tokens", 0.0)),
        reverse=True,
    )[:10]

    summary["top_pages_by_takahashi_tokens"] = sorted(
        hybrid_pages,
        key=lambda p: float(p.get("hybrid_taka_tokens", 0.0)),
        reverse=True,
    )[:10]

    summary["top_fields_by_spread"] = sorted(
        hybrid_fields,
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
        "page_coherence_mean": pages.get("coherence_index", {}).get("mean", 0.0),
        "page_delta_phi_mean": pages.get("delta_phi_mean", {}).get("mean", 0.0),
        "eva_tokens_mean":     pages.get("eva_tokens", {}).get("mean", 0.0),
        "takahashi_tokens_mean": pages.get("takahashi_tokens", {}).get("mean", 0.0),
        "delta_tokens_mean":   pages.get("delta_tokens", {}).get("mean", 0.0),
        "field_spread_mean":   fields.get("num_pages", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir = os.path.join(root, "data")

    meaning_v5_3 = os.path.join(data_dir, "meaning_v5_3")
    meaning_v5_4 = os.path.join(data_dir, "meaning_v5_4")
    meaning_v5_5 = os.path.join(data_dir, "meaning_v5_5")
    hybrid_dir   = os.path.join(data_dir, "hybrid_v1_0")

    graph_path   = os.path.join(meaning_v5_5, "manuscript_graph_v5_5.json")
    hybrid_path  = os.path.join(hybrid_dir, "hybrid_corpus_v1_0.json")

    out_graph_path   = os.path.join(meaning_v5_5, "hybrid_manuscript_graph_v5_5b.json")
    out_summary_path = os.path.join(meaning_v5_5, "hybrid_manuscript_summary_v5_5b.json")
    out_ledger_path  = os.path.join(meaning_v5_5, "hybrid_manuscript_ledger_v5_5b.jsonl")

    manuscript_pages, manuscript_fields, manuscript_edges = load_manuscript_graph(graph_path)
    hybrid_corpus = load_hybrid_corpus(hybrid_path)

    # Glyph seed: image used only as symbolic signature, not in metrics
    glyph_seed_meta = {
        "mode": "external_image_signature",
        "tag": "hybrid_corpus_seed_v1_0",
        "note": "Image used as glyph seed only; no effect on tokens or coherence metrics.",
    }

    hybrid_pages, hybrid_fields = build_hybrid_graph(
        manuscript_pages,
        manuscript_fields,
        manuscript_edges,
        hybrid_corpus,
    )

    summary = summarize_hybrid(hybrid_pages, hybrid_fields, glyph_seed_meta)
    led = ledger_record(summary)

    out_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "pages": hybrid_pages,
        "fields": hybrid_fields,
    }

    save_json(out_graph_path, out_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid manuscript graph v5.5B   ->", out_graph_path)
    print("Hybrid manuscript summary v5.5B ->", out_summary_path)
    print("Hybrid manuscript ledger v5.5B  ->", out_ledger_path)

if __name__ == "__main__":
    main()
