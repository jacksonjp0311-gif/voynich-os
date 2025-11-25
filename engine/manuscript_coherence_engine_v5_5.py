#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v5.5 - Manuscript Coherence Engine (auto-written by All-One PS)

import os
import json
import math
import statistics
import datetime
from collections import defaultdict

VERSION = "v5_5"

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

# -----------------------------
# Normalization helpers
# -----------------------------

def load_paragraph_fields(paragraph_fields_path):
    data = load_json(paragraph_fields_path, default={})
    fields = data.get("fields", [])
    normalized = []
    for f in fields:
        fid = str(f.get("field_id", ""))
        sids = [str(s) for s in f.get("sentence_ids", [])]
        metrics = f.get("metrics", {})
        dphi = float(metrics.get("delta_phi_field", 0.0))
        fri  = float(metrics.get("field_resonance_index", 0.0))
        normalized.append({
            "field_id": fid,
            "sentence_ids": sids,
            "delta_phi_field": dphi,
            "field_resonance_index": fri,
        })
    return normalized

def load_page_fields(page_fields_path):
    data = load_json(page_fields_path, default={})
    pages = data.get("pages", [])
    normalized = []
    for p in pages:
        pid = str(p.get("page_id", ""))
        sids = [str(s) for s in p.get("sentence_ids", [])]
        fids = [str(f) for f in p.get("field_ids", [])]
        metrics = p.get("metrics", {})
        num_sentences = int(metrics.get("num_sentences", 0))
        num_fields    = int(metrics.get("num_fields", 0))
        coverage      = float(metrics.get("coverage_ratio", 0.0))
        coherence     = float(metrics.get("coherence_index", 0.0))
        dphi_mean     = float(metrics.get("delta_phi_mean", 0.0))
        normalized.append({
            "page_id": pid,
            "sentence_ids": sids,
            "field_ids": fids,
            "metrics": {
                "num_sentences": num_sentences,
                "num_fields": num_fields,
                "coverage_ratio": coverage,
                "coherence_index": coherence,
                "delta_phi_mean": dphi_mean,
            },
        })
    return normalized

# -----------------------------
# Core synthesis
# -----------------------------

def build_bipartite_graph(paragraph_fields, page_fields):
    # field_id -> field metrics
    field_metric_map = {}
    for f in paragraph_fields:
        field_metric_map[f["field_id"]] = {
            "delta_phi_field": f["delta_phi_field"],
            "field_resonance_index": f["field_resonance_index"],
        }

    # page_id -> page metrics
    page_metric_map = {}
    page_field_links = []   # edges page <-> field
    field_to_pages = defaultdict(set)

    for p in page_fields:
        pid = p["page_id"]
        page_metric_map[pid] = p["metrics"]
        for fid in p["field_ids"]:
            page_field_links.append({"page_id": pid, "field_id": fid})
            field_to_pages[fid].add(pid)

    # field-level manuscript metrics
    field_nodes = []
    for fid, pages in field_to_pages.items():
        metrics = field_metric_map.get(fid, {})
        dphi = float(metrics.get("delta_phi_field", 0.0))
        fri  = float(metrics.get("field_resonance_index", 0.0))
        field_nodes.append({
            "field_id": fid,
            "num_pages": len(pages),
            "delta_phi_field": dphi,
            "field_resonance_index": fri,
            "page_ids": sorted(list(pages)),
        })

    # page nodes (flattened for output)
    page_nodes = []
    for p in page_fields:
        m = p["metrics"]
        page_nodes.append({
            "page_id": p["page_id"],
            "num_sentences": m.get("num_sentences", 0),
            "num_fields": m.get("num_fields", 0),
            "coverage_ratio": m.get("coverage_ratio", 0.0),
            "coherence_index": m.get("coherence_index", 0.0),
            "delta_phi_mean": m.get("delta_phi_mean", 0.0),
        })

    return page_nodes, field_nodes, page_field_links

def safe_mean(xs):
    xs = list(xs)
    if not xs:
        return 0.0
    return float(statistics.mean(xs))

def safe_min(xs):
    xs = list(xs)
    if not xs:
        return 0.0
    return float(min(xs))

def safe_max(xs):
    xs = list(xs)
    if not xs:
        return 0.0
    return float(max(xs))

def summarize_manuscript(page_nodes, field_nodes):
    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": len(page_nodes),
        "num_fields": len(field_nodes),
    }

    if not page_nodes and not field_nodes:
        return summary

    # Page metrics
    coverage_vals = [float(p.get("coverage_ratio", 0.0)) for p in page_nodes]
    coherence_vals = [float(p.get("coherence_index", 0.0)) for p in page_nodes]
    dphi_page_vals = [float(p.get("delta_phi_mean", 0.0)) for p in page_nodes]

    summary["pages"] = {
        "coverage_ratio": {
            "mean": safe_mean(coverage_vals),
            "min": safe_min(coverage_vals),
            "max": safe_max(coverage_vals),
        },
        "coherence_index": {
            "mean": safe_mean(coherence_vals),
            "min": safe_min(coherence_vals),
            "max": safe_max(coherence_vals),
        },
        "delta_phi_mean": {
            "mean": safe_mean(dphi_page_vals),
            "min": safe_min(dphi_page_vals),
            "max": safe_max(dphi_page_vals),
        },
    }

    # Field metrics
    field_page_counts = [int(f.get("num_pages", 0)) for f in field_nodes]
    field_fri_vals = [float(f.get("field_resonance_index", 0.0)) for f in field_nodes]
    field_dphi_vals = [float(f.get("delta_phi_field", 0.0)) for f in field_nodes]

    summary["fields"] = {
        "num_pages": {
            "mean": safe_mean(field_page_counts),
            "min": safe_min(field_page_counts),
            "max": safe_max(field_page_counts),
        },
        "field_resonance_index": {
            "mean": safe_mean(field_fri_vals),
            "min": safe_min(field_fri_vals),
            "max": safe_max(field_fri_vals),
        },
        "delta_phi_field": {
            "mean": safe_mean(field_dphi_vals),
            "min": safe_min(field_dphi_vals),
            "max": safe_max(field_dphi_vals),
        },
    }

    # Identify top pages and fields by coherence / spread
    top_pages = sorted(
        page_nodes,
        key=lambda p: float(p.get("coherence_index", 0.0)),
        reverse=True,
    )
    top_fields = sorted(
        field_nodes,
        key=lambda f: (int(f.get("num_pages", 0)), float(f.get("field_resonance_index", 0.0))),
        reverse=True,
    )

    summary["top_pages_by_coherence"] = top_pages[:10]
    summary["top_fields_by_spread"] = top_fields[:10]

    return summary

def ledger_record(summary):
    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_pages": summary.get("num_pages", 0),
        "num_fields": summary.get("num_fields", 0),
        "page_coherence_mean": summary.get("pages", {}).get("coherence_index", {}).get("mean", 0.0),
        "field_spread_mean": summary.get("fields", {}).get("num_pages", {}).get("mean", 0.0),
    }

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    meaning_v5_3 = os.path.join(root, "data", "meaning_v5_3")
    meaning_v5_4 = os.path.join(root, "data", "meaning_v5_4")
    meaning_v5_5 = os.path.join(root, "data", "meaning_v5_5")

    paragraph_fields_path = os.path.join(meaning_v5_3, "paragraph_fields_v5_3.json")
    page_fields_path      = os.path.join(meaning_v5_4, "page_fields_v5_4.json")

    manuscript_graph_path   = os.path.join(meaning_v5_5, "manuscript_graph_v5_5.json")
    manuscript_summary_path = os.path.join(meaning_v5_5, "manuscript_summary_v5_5.json")
    manuscript_ledger_path  = os.path.join(meaning_v5_5, "manuscript_ledger_v5_5.jsonl")

    paragraph_fields = load_paragraph_fields(paragraph_fields_path) or []
    page_fields = load_page_fields(page_fields_path) or []

    page_nodes, field_nodes, page_field_edges = build_bipartite_graph(paragraph_fields, page_fields)
    summary = summarize_manuscript(page_nodes, field_nodes)
    ledger = ledger_record(summary)

    save_json(manuscript_graph_path, {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "pages": page_nodes,
        "fields": field_nodes,
        "edges": page_field_edges,
    })

    save_json(manuscript_summary_path, summary)
    append_jsonl(manuscript_ledger_path, ledger)

    print("Manuscript graph v5.5    ->", manuscript_graph_path)
    print("Manuscript summary v5.5  ->", manuscript_summary_path)
    print("Manuscript ledger v5.5   ->", manuscript_ledger_path)

if __name__ == "__main__":
    main()
