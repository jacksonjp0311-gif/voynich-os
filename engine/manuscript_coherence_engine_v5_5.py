#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v5.5 — Manuscript Coherence Engine (auto-written by All-One PS)

import os, json, math, datetime
from collections import defaultdict

VERSION = "v5_5"

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_json(path, default=None):
    if not os.path.isfile(path): return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def append_jsonl(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

# Normalize paragraph fields (v5.3)
def load_paragraph_fields(path):
    data = load_json(path, default={})
    fields = data.get("fields", [])
    out = []
    for f in fields:
        out.append({
            "field_id": str(f.get("field_id", "")),
            "sentence_ids": [str(s) for s in f.get("sentence_ids", [])],
            "delta_phi_field": float(f.get("metrics", {}).get("delta_phi_field", 0.0)),
            "field_resonance_index": float(f.get("metrics", {}).get("field_resonance_index", 0.0)),
        })
    return out

# Normalize page fields (v5.4)
def load_page_fields(path):
    data = load_json(path, default={})
    pages = data.get("pages", [])
    out = []
    for p in pages:
        m = p.get("metrics", {})
        out.append({
            "page_id": str(p.get("page_id", "")),
            "sentence_ids": [str(s) for s in p.get("sentence_ids", [])],
            "field_ids": [str(f) for f in p.get("field_ids", [])],
            "metrics": {
                "num_sentences": int(m.get("num_sentences", 0)),
                "num_fields": int(m.get("num_fields", 0)),
                "coverage_ratio": float(m.get("coverage_ratio", 0.0)),
                "coherence_index": float(m.get("coherence_index", 0.0)),
                "delta_phi_mean": float(m.get("delta_phi_mean", 0.0)),
            },
        })
    return out

# Build manuscript bipartite structure
def build_graph(par_fields, page_fields):
    # field-level map
    fmetrics = {f["field_id"]: f for f in par_fields}

    # page-level
    page_nodes = []
    edges = []
    field_to_pages = defaultdict(list)

    for p in page_fields:
        page_nodes.append({
            "page_id": p["page_id"],
            "num_sentences": p["metrics"]["num_sentences"],
            "num_fields": p["metrics"]["num_fields"],
            "coverage_ratio": p["metrics"]["coverage_ratio"],
            "coherence_index": p["metrics"]["coherence_index"],
            "delta_phi_mean": p["metrics"]["delta_phi_mean"],
        })
        for fid in p["field_ids"]:
            edges.append({"page_id": p["page_id"], "field_id": fid})
            field_to_pages[fid].append(p["page_id"])

    # field nodes
    field_nodes = []
    for fid, pages in field_to_pages.items():
        fm = fmetrics.get(fid, {})
        field_nodes.append({
            "field_id": fid,
            "num_pages": len(pages),
            "page_ids": sorted(pages),
            "delta_phi_field": float(fm.get("delta_phi_field", 0.0)),
            "field_resonance_index": float(fm.get("field_resonance_index", 0.0)),
        })

    return page_nodes, field_nodes, edges

# Summaries
def summarize(page_nodes, field_nodes):
    import statistics
    def safe(vals, fn, default=0.0):
        vals = list(vals)
        if not vals: return default
        try: return float(fn(vals))
        except: return default

    out = {
        "version": VERSION,
        "timestamp_utc": now_utc(),
        "num_pages": len(page_nodes),
        "num_fields": len(field_nodes),
        "pages": {},
        "fields": {},
    }

    # page stats
    cr = [p["coverage_ratio"] for p in page_nodes]
    ci = [p["coherence_index"] for p in page_nodes]
    dp = [p["delta_phi_mean"] for p in page_nodes]

    out["pages"]["coverage_ratio"] = {
        "mean": safe(cr, statistics.mean),
        "min": safe(cr, min),
        "max": safe(cr, max),
    }
    out["pages"]["coherence_index"] = {
        "mean": safe(ci, statistics.mean),
        "min": safe(ci, min),
        "max": safe(ci, max),
    }
    out["pages"]["delta_phi_mean"] = {
        "mean": safe(dp, statistics.mean),
        "min": safe(dp, min),
        "max": safe(dp, max),
    }

    # field stats
    npages = [f["num_pages"] for f in field_nodes]
    fri    = [f["field_resonance_index"] for f in field_nodes]
    df     = [f["delta_phi_field"] for f in field_nodes]

    out["fields"]["num_pages"] = {
        "mean": safe(npages, statistics.mean),
        "min": safe(npages, min),
        "max": safe(npages, max),
    }
    out["fields"]["field_resonance_index"] = {
        "mean": safe(fri, statistics.mean),
        "min": safe(fri, min),
        "max": safe(fri, max),
    }
    out["fields"]["delta_phi_field"] = {
        "mean": safe(df, statistics.mean),
        "min": safe(df, min),
        "max": safe(df, max),
    }

    return out

def ledger(summary):
    return {
        "version": VERSION,
        "timestamp_utc": summary["timestamp_utc"],
        "num_pages": summary["num_pages"],
        "num_fields": summary["num_fields"],
        "page_coherence_mean": summary["pages"]["coherence_index"]["mean"],
        "field_spread_mean": summary["fields"]["num_pages"]["mean"],
    }

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    pf_path = os.path.join(root,"data","meaning_v5_3","paragraph_fields_v5_3.json")
    pg_path = os.path.join(root,"data","meaning_v5_4","page_fields_v5_4.json")
    out_dir = os.path.join(root,"data","meaning_v5_5")

    par_fields = load_paragraph_fields(pf_path)
    page_fields = load_page_fields(pg_path)

    pages, fields, edges = build_graph(par_fields, page_fields)
    summary = summarize(pages, fields)
    led = ledger(summary)

    save_json(os.path.join(out_dir,"manuscript_graph_v5_5.json"),
              {"version":VERSION,"timestamp_utc":now_utc(),
               "pages":pages,"fields":fields,"edges":edges})

    save_json(os.path.join(out_dir,"manuscript_summary_v5_5.json"), summary)
    append_jsonl(os.path.join(out_dir,"manuscript_ledger_v5_5.jsonl"), led)

    print("Manuscript graph v5.5    ->", os.path.join(out_dir,"manuscript_graph_v5_5.json"))
    print("Manuscript summary v5.5  ->", os.path.join(out_dir,"manuscript_summary_v5_5.json"))
    print("Manuscript ledger v5.5   ->", os.path.join(out_dir,"manuscript_ledger_v5_5.jsonl"))

if __name__ == "__main__":
    main()
