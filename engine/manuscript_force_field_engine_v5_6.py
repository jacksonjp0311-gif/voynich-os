#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v5.6 — Manuscript Force-Field Engine (Hybrid Field Mode)
# Auto-written by All-One PS (v5.6)

import os
import json
import datetime
from collections import defaultdict

VERSION = "v5_6"

# ─────────────────────────────
# Basic I/O helpers
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

# ─────────────────────────────
# Force-field construction
# ─────────────────────────────
def build_stub_graph():
    """Fallback when v5.5 graph is missing: single GLOBAL_PAGE / meta field."""
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

def normalize_graph(graph_data):
    """Normalize manuscript graph into pages, fields, edges."""
    if not graph_data or "pages" not in graph_data or "fields" not in graph_data:
        graph_data = build_stub_graph()

    pages_raw = graph_data.get("pages", [])
    fields_raw = graph_data.get("fields", [])
    edges_raw = graph_data.get("edges", [])

    pages = []
    for p in pages_raw:
        pages.append({
            "page_id": str(p.get("page_id", "")),
            "num_sentences": int(p.get("num_sentences", 0)),
            "num_fields": int(p.get("num_fields", 0)),
            "coverage_ratio": float(p.get("coverage_ratio", 0.0)),
            "coherence_index": float(p.get("coherence_index", 0.0)),
            "delta_phi_mean": float(p.get("delta_phi_mean", 0.0)),
        })

    fields = []
    for f in fields_raw:
        fields.append({
            "field_id": str(f.get("field_id", "")),
            "num_pages": int(f.get("num_pages", 0)),
            "page_ids": [str(pid) for pid in f.get("page_ids", [])],
            "delta_phi_field": float(f.get("delta_phi_field", 0.0)),
            "field_resonance_index": float(f.get("field_resonance_index", 0.0)),
        })

    edges = []
    for e in edges_raw:
        edges.append({
            "page_id": str(e.get("page_id", "")),
            "field_id": str(e.get("field_id", "")),
        })

    return pages, fields, edges

def build_force_field(pages, fields, edges, target_h7=0.70):
    """
    Hybrid field mode:
      • Local page geometry: coherence_index, delta_phi_mean
      • Manuscript connectivity: neighbors, field degrees
      • Force potential per page: Codex-style simplification:
          F_page = coherence_index / (1 + |ΔΦ_page - ΔΦ_target|)
      where ΔΦ_target is linked to H7 ~ 0.70.
    """
    # Map: page_id -> page index / data
    page_map = {p["page_id"]: p for p in pages}

    # Build field → pages mapping and page → fields mapping
    field_to_pages = defaultdict(set)
    page_to_fields = defaultdict(set)
    for e in edges:
        pid = e["page_id"]
        fid = e["field_id"]
        if pid:
            page_to_fields[pid].add(fid)
        if fid:
            field_to_pages[fid].add(pid)

    # Build page neighbor graph: pages connected if they share at least one field
    page_neighbors = defaultdict(set)
    for fid, pids in field_to_pages.items():
        pids_list = list(pids)
        n = len(pids_list)
        for i in range(n):
            for j in range(i + 1, n):
                a = pids_list[i]
                b = pids_list[j]
                page_neighbors[a].add(b)
                page_neighbors[b].add(a)

    # Build force-field pages
    ff_pages = []
    for pid, pdata in page_map.items():
        neighbors = sorted(list(page_neighbors.get(pid, set())))
        num_neighbors = len(neighbors)
        incident_fields = sorted(list(page_to_fields.get(pid, set())))
        num_fields = len(incident_fields)

        local_c = float(pdata.get("coherence_index", 0.0))
        local_dphi = float(pdata.get("delta_phi_mean", 0.0))

        # Codex-inspired potential:
        #   ΔΦ_target ≈ 0 (alignment), but we bias via H7 by treating it as a
        #   "comfort radius" around 0.70.
        #   Here we just use |ΔΦ_page - 0.0| with a softening factor around H7.
        delta_shift = abs(local_dphi - 0.0)
        denom = 1.0 + delta_shift / max(target_h7, 1e-6)
        force_potential = local_c / denom

        ff_pages.append({
            "page_id": pid,
            "neighbors": neighbors,
            "num_neighbors": num_neighbors,
            "fields": incident_fields,
            "num_fields": num_fields,
            "coherence_index": local_c,
            "delta_phi_mean": local_dphi,
            "force_potential": float(force_potential),
        })

    # Attach field-side view with per-field ΔΦ and resonance
    ff_fields = []
    for f in fields:
        fid = f["field_id"]
        page_ids = sorted(list(field_to_pages.get(fid, set())))
        ff_fields.append({
            "field_id": fid,
            "page_ids": page_ids,
            "num_pages": len(page_ids),
            "delta_phi_field": f.get("delta_phi_field", 0.0),
            "field_resonance_index": f.get("field_resonance_index", 0.0),
        })

    return ff_pages, ff_fields

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────
def safe_stats(values):
    vals = [float(v) for v in values]
    if not vals:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": float(sum(vals) / len(vals)),
        "min": float(min(vals)),
        "max": float(max(vals)),
    }

def summarize_force_field(ff_pages, ff_fields):
    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": len(ff_pages),
        "num_fields": len(ff_fields),
    }

    # Page stats
    coh = [p["coherence_index"] for p in ff_pages]
    dphi = [p["delta_phi_mean"] for p in ff_pages]
    force = [p["force_potential"] for p in ff_pages]
    deg = [p["num_neighbors"] for p in ff_pages]
    fdeg = [p["num_fields"] for p in ff_pages]

    summary["pages"] = {
        "coherence_index": safe_stats(coh),
        "delta_phi_mean": safe_stats(dphi),
        "force_potential": safe_stats(force),
        "degree": safe_stats(deg),
        "field_degree": safe_stats(fdeg),
    }

    # Field stats
    field_pages = [f["num_pages"] for f in ff_fields]
    field_fri = [f["field_resonance_index"] for f in ff_fields]
    field_dphi = [f["delta_phi_field"] for f in ff_fields]

    summary["fields"] = {
        "num_pages": safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field": safe_stats(field_dphi),
    }

    # Top structures
    summary["top_pages_by_force"] = sorted(
        ff_pages,
        key=lambda p: float(p.get("force_potential", 0.0)),
        reverse=True,
    )[:10]

    summary["top_fields_by_spread"] = sorted(
        ff_fields,
        key=lambda f: int(f.get("num_pages", 0)),
        reverse=True,
    )[:10]

    return summary

def ledger_record(summary):
    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_pages": summary.get("num_pages", 0),
        "num_fields": summary.get("num_fields", 0),
        "page_force_mean": summary.get("pages", {})
                                   .get("force_potential", {})
                                   .get("mean", 0.0),
        "page_degree_mean": summary.get("pages", {})
                                    .get("degree", {})
                                    .get("mean", 0.0),
        "field_spread_mean": summary.get("fields", {})
                                     .get("num_pages", {})
                                     .get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────
def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    meaning_v5_5 = os.path.join(root, "data", "meaning_v5_5")
    meaning_v5_6 = os.path.join(root, "data", "meaning_v5_6")

    graph_path = os.path.join(meaning_v5_5, "manuscript_graph_v5_5.json")

    force_field_path  = os.path.join(meaning_v5_6, "manuscript_force_field_v5_6.json")
    force_summary_path = os.path.join(meaning_v5_6, "manuscript_force_summary_v5_6.json")
    force_ledger_path  = os.path.join(meaning_v5_6, "manuscript_force_ledger_v5_6.jsonl")

    graph_data = load_json(graph_path, default=None)

    pages, fields, edges = normalize_graph(graph_data)
    ff_pages, ff_fields = build_force_field(pages, fields, edges)
    summary = summarize_force_field(ff_pages, ff_fields)
    ledger = ledger_record(summary)

    out_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "pages": ff_pages,
        "fields": ff_fields,
    }

    save_json(force_field_path, out_obj)
    save_json(force_summary_path, summary)
    append_jsonl(force_ledger_path, ledger)

    print("Manuscript force-field v5.6      ->", force_field_path)
    print("Manuscript force summary v5.6    ->", force_summary_path)
    print("Manuscript force ledger v5.6     ->", force_ledger_path)

if __name__ == "__main__":
    main()
