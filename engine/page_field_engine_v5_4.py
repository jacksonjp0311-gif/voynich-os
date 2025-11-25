#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v5.4 — Page-Level Field Synthesis Engine (auto-written by All-One PS)

import os
import json
import math
import statistics
import datetime
from collections import defaultdict

VERSION = "v5_4"

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

def build_sentence_to_fields(paragraph_fields):
    sentence_to_fields = defaultdict(list)
    for field in paragraph_fields:
        fid = str(field.get("field_id", ""))
        sids = field.get("sentence_ids", [])
        for sid in sids:
            sid_str = str(sid)
            if fid not in sentence_to_fields[sid_str]:
                sentence_to_fields[sid_str].append(fid)
    return sentence_to_fields

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

def load_folio_sentence_mapping(folio_dir):
    mapping = {}
    if not os.path.isdir(folio_dir):
        return mapping
    for fname in os.listdir(folio_dir):
        if not fname.lower().endswith(".json"):
            continue
        folio_id = os.path.splitext(fname)[0]
        path = os.path.join(folio_dir, fname)
        doc = load_json(path, default=None)
        if doc is None:
            continue
        sentences = []
        # Try common structures
        if isinstance(doc, dict) and isinstance(doc.get("sentences"), list):
            seq = doc["sentences"]
        elif isinstance(doc, list):
            seq = doc
        else:
            seq = []
        for item in seq:
            if isinstance(item, dict):
                sid = item.get("id") or item.get("sentence_id") or item.get("sid")
                if sid:
                    sentences.append(str(sid))
            elif isinstance(item, str):
                sentences.append(item)
        if sentences:
            # Deduplicate while preserving order
            seen = set()
            uniq = []
            for s in sentences:
                if s not in seen:
                    seen.add(s)
                    uniq.append(s)
            mapping[folio_id] = uniq
    return mapping

def compute_page_fields(paragraph_fields, sentence_to_fields, folio_map):
    # If no folio mapping, make a synthetic page with all sentences
    if not folio_map:
        all_sentences = set()
        for field in paragraph_fields:
            for sid in field["sentence_ids"]:
                all_sentences.add(sid)
        folio_map = {"GLOBAL_PAGE": sorted(all_sentences)}

    # Build quick lookup for field metrics
    field_metrics = {}
    for f in paragraph_fields:
        field_metrics[f["field_id"]] = {
            "delta_phi_field": f["delta_phi_field"],
            "field_resonance_index": f["field_resonance_index"],
        }

    pages = []
    page_to_fields = defaultdict(set)

    for page_id, sids in folio_map.items():
        sentence_ids = [str(s) for s in sids]
        page_sentence_set = set(sentence_ids)

        # Determine which fields appear on this page
        page_field_ids = set()
        covered_sentences = 0
        for sid in page_sentence_set:
            if sid in sentence_to_fields:
                covered_sentences += 1
                for fid in sentence_to_fields[sid]:
                    page_field_ids.add(fid)

        num_sentences = len(page_sentence_set)
        num_fields = len(page_field_ids)
        coverage_ratio = (covered_sentences / num_sentences) if num_sentences > 0 else 0.0

        # Aggregate field metrics for fields on this page
        dphi_vals = []
        fri_vals = []
        for fid in page_field_ids:
            m = field_metrics.get(fid)
            if m is None:
                continue
            dphi_vals.append(m.get("delta_phi_field", 0.0))
            fri_vals.append(m.get("field_resonance_index", 0.0))

        def safe_mean(xs):
            if not xs:
                return 0.0
            return float(statistics.mean(xs))

        coherence_index = safe_mean(fri_vals)
        dphi_mean = safe_mean(dphi_vals)

        pages.append({
            "page_id": str(page_id),
            "sentence_ids": sorted(list(page_sentence_set)),
            "field_ids": sorted(list(page_field_ids)),
            "metrics": {
                "num_sentences": num_sentences,
                "num_fields": num_fields,
                "coverage_ratio": coverage_ratio,
                "coherence_index": coherence_index,
                "delta_phi_mean": dphi_mean,
            },
        })

        for fid in page_field_ids:
            page_to_fields[page_id].add(fid)

    return pages, page_to_fields

def build_page_graph(page_to_fields):
    # field_id -> set(page_ids)
    field_to_pages = defaultdict(set)
    for page_id, fields in page_to_fields.items():
        for fid in fields:
            field_to_pages[fid].add(page_id)

    edges = defaultdict(float)
    for fid, pages in field_to_pages.items():
        pages_list = sorted(list(pages))
        n = len(pages_list)
        for i in range(n):
            for j in range(i + 1, n):
                a = pages_list[i]
                b = pages_list[j]
                key = (a, b)
                edges[key] += 1.0

    edge_list = []
    for (a, b), w in edges.items():
        edge_list.append({
            "page_a": str(a),
            "page_b": str(b),
            "weight": float(w),
            "version": VERSION,
        })
    return edge_list

def summarize_pages(pages):
    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": len(pages),
    }
    if not pages:
        return summary

    coverage = []
    coherence = []
    dphi_mean_vals = []

    for p in pages:
        m = p.get("metrics", {})
        coverage.append(float(m.get("coverage_ratio", 0.0)))
        coherence.append(float(m.get("coherence_index", 0.0)))
        dphi_mean_vals.append(float(m.get("delta_phi_mean", 0.0)))

    def safe_mean(xs):
        if not xs:
            return 0.0
        return float(statistics.mean(xs))

    def safe_min(xs):
        if not xs:
            return 0.0
        return float(min(xs))

    def safe_max(xs):
        if not xs:
            return 0.0
        return float(max(xs))

    summary["coverage_ratio"] = {
        "mean": safe_mean(coverage),
        "min": safe_min(coverage),
        "max": safe_max(coverage),
    }
    summary["coherence_index"] = {
        "mean": safe_mean(coherence),
        "min": safe_min(coherence),
        "max": safe_max(coherence),
    }
    summary["delta_phi_mean"] = {
        "mean": safe_mean(dphi_mean_vals),
        "min": safe_min(dphi_mean_vals),
        "max": safe_max(dphi_mean_vals),
    }
    return summary

def ledger_record_from_summary(summary):
    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_pages": summary.get("num_pages", 0),
        "coverage_mean": summary.get("coverage_ratio", {}).get("mean", 0.0),
        "coherence_mean": summary.get("coherence_index", {}).get("mean", 0.0),
        "delta_phi_mean_mean": summary.get("delta_phi_mean", {}).get("mean", 0.0),
    }

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    meaning_v5_3 = os.path.join(root, "data", "meaning_v5_3")
    meaning_v5_4 = os.path.join(root, "data", "meaning_v5_4")
    folio_dir    = os.path.join(root, "data", "folio_outputs")

    paragraph_fields_path = os.path.join(meaning_v5_3, "paragraph_fields_v5_3.json")

    page_fields_path  = os.path.join(meaning_v5_4, "page_fields_v5_4.json")
    page_graph_path   = os.path.join(meaning_v5_4, "page_graph_v5_4.json")
    page_summary_path = os.path.join(meaning_v5_4, "page_summary_v5_4.json")
    page_ledger_path  = os.path.join(meaning_v5_4, "page_ledger_v5_4.jsonl")

    paragraph_fields = load_paragraph_fields(paragraph_fields_path)
    sentence_to_fields = build_sentence_to_fields(paragraph_fields)
    folio_map = load_folio_sentence_mapping(folio_dir)

    pages, page_to_fields = compute_page_fields(paragraph_fields, sentence_to_fields, folio_map)
    edges = build_page_graph(page_to_fields)
    summary = summarize_pages(pages)
    ledger_rec = ledger_record_from_summary(summary)

    save_json(page_fields_path, {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "pages": pages,
    })
    save_json(page_graph_path, {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "edges": edges,
    })
    save_json(page_summary_path, summary)
    append_jsonl(page_ledger_path, ledger_rec)

    print("Page fields v5.4        ->", page_fields_path)
    print("Page graph v5.4         ->", page_graph_path)
    print("Page summary v5.4       ->", page_summary_path)
    print("Page ledger v5.4 append ->", page_ledger_path)

if __name__ == "__main__":
    main()
