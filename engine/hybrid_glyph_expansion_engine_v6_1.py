#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS v6.1 — Hybrid Glyph Expansion Engine (Image → Glyph Seeds → Fields)
# Auto-written by All-One PS (v6.1)

import os
import json
import math
import datetime

VERSION = "v6_1"

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
# Load v6.0 glyph field
# ─────────────────────────────

def build_stub_glyph_field():
    return {
        "version": "v6_0_stub",
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": {},
        "pages": [
            {
                "page_id": "GLOBAL_PAGE",
                "num_sentences": 0,
                "num_fields": 1,
                "coverage_ratio": 0.0,
                "coherence_index": 0.0,
                "delta_phi_mean": 0.0,
                "force_field_neighbors": 0,
                "force_field_potential": 0.0,
                "force_field_fields": 1,
                "hybrid_eva_tokens": 0,
                "hybrid_takahashi_tokens": 0,
                "hybrid_delta_tokens": 0,
                "hybrid_edge_degree": 0,
                "glyph_grid_score": 0.0,
                "hybrid_intensity": 0.0,
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

def load_glyph_field(path):
    data = load_json(path, default=None)
    if not data or "pages" not in data or "fields" not in data:
        data = build_stub_glyph_field()
    return data

# ─────────────────────────────
# Page ↔ field index
# ─────────────────────────────

def build_page_to_fields(fields):
    mapping = {}
    for f in fields:
        fid = str(f.get("field_id", ""))
        for pid in f.get("page_ids", []):
            pid_str = str(pid)
            if not pid_str:
                continue
            if pid_str not in mapping:
                mapping[pid_str] = []
            mapping[pid_str].append(fid)
    return mapping

# ─────────────────────────────
# Hybrid glyph expansion
# ─────────────────────────────

def build_glyph_expansion(glyph_field_obj, glyph_seed_meta):
    pages  = glyph_field_obj.get("pages", [])
    fields = glyph_field_obj.get("fields", [])

    page_to_fields = build_page_to_fields(fields)

    glyph_pages = []
    glyph_seeds = []

    for p in pages:
        pid = str(p.get("page_id", "")) or "UNKNOWN_PAGE"

        cov   = float(p.get("coverage_ratio", 0.0))
        coh   = float(p.get("coherence_index", 0.0))
        dphi  = float(p.get("delta_phi_mean", 0.0))
        ggrid = float(p.get("glyph_grid_score", 0.0))
        force = float(p.get("force_field_potential", 0.0))

        eva_tokens   = int(p.get("hybrid_eva_tokens", 0))
        taka_tokens  = int(p.get("hybrid_takahashi_tokens", 0))
        delta_tokens = int(p.get("hybrid_delta_tokens", 0))

        # Codex-style heuristic:
        #   base_n ~ sqrt(1 + glyph_grid_score) scaled by coverage & coherence
        #   bounded to [1, 128] for stability.
        base_mag = max(ggrid, 0.0)
        factor = 1.0 + max(cov, 0.0) + max(coh, 0.0)
        n_seeds = int(round(factor * math.sqrt(1.0 + base_mag)))
        if n_seeds < 1:
            n_seeds = 1
        if n_seeds > 128:
            n_seeds = 128

        page_fields = page_to_fields.get(pid, [])

        glyph_ids_for_page = []

        total_tokens = float(max(eva_tokens + taka_tokens, 0))
        for k in range(n_seeds):
            t = (k + 0.5) / float(n_seeds)  # normalized index in [0,1)
            # Smooth harmonic modulation across page
            harmonic = 0.5 + 0.5 * math.cos(2.0 * math.pi * (t - 0.5))

            intensity = (
                (1.0 + base_mag)
                * (1.0 + coh)
                * (1.0 + force)
                * math.sqrt(1.0 + total_tokens)
                * harmonic
            )

            gid = f"{pid}_g{str(k).zfill(3)}"
            glyph_ids_for_page.append(gid)

            glyph_seeds.append({
                "glyph_id": gid,
                "page_id": pid,
                "fields": page_fields,
                "rank_in_page": k,
                "normalized_index": float(t),
                "intensity": float(intensity),
                "coverage_ratio": cov,
                "coherence_index": coh,
                "delta_phi_mean": dphi,
            })

        glyph_pages.append({
            "page_id": pid,
            "num_glyph_seeds": n_seeds,
            "glyph_seed_ids": glyph_ids_for_page,
            "glyph_grid_score": ggrid,
            "coverage_ratio": cov,
            "coherence_index": coh,
            "delta_phi_mean": dphi,
            "hybrid_eva_tokens": eva_tokens,
            "hybrid_takahashi_tokens": taka_tokens,
            "hybrid_delta_tokens": delta_tokens,
        })

    out_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "glyph_seed": glyph_seed_meta,
        "pages": glyph_pages,
        "glyph_seeds": glyph_seeds,
        "fields": fields,
    }
    return out_obj

# ─────────────────────────────
# Summary + ledger
# ─────────────────────────────

def summarize_expansion(expansion_obj):
    pages = expansion_obj.get("pages", [])
    seeds = expansion_obj.get("glyph_seeds", [])
    fields = expansion_obj.get("fields", [])

    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_pages": len(pages),
        "num_fields": len(fields),
        "num_glyph_seeds": len(seeds),
        "glyph_seed": expansion_obj.get("glyph_seed", {}),
    }

    glyphs_per_page = [p["num_glyph_seeds"] for p in pages] if pages else []
    ggrid = [p["glyph_grid_score"] for p in pages] if pages else []
    cov   = [p["coverage_ratio"] for p in pages] if pages else []
    coh   = [p["coherence_index"] for p in pages] if pages else []
    dphi  = [p["delta_phi_mean"] for p in pages] if pages else []

    intensities = [s["intensity"] for s in seeds] if seeds else []

    summary["pages"] = {
        "glyphs_per_page": safe_stats(glyphs_per_page),
        "glyph_grid_score": safe_stats(ggrid),
        "coverage_ratio": safe_stats(cov),
        "coherence_index": safe_stats(coh),
        "delta_phi_mean": safe_stats(dphi),
    }

    summary["glyph_seeds"] = {
        "intensity": safe_stats(intensities),
    }

    field_pages = [f.get("num_pages", 0) for f in fields]
    field_fri   = [f.get("field_resonance_index", 0.0) for f in fields]
    field_dphi  = [f.get("delta_phi_field", 0.0) for f in fields]

    summary["fields"] = {
        "num_pages": safe_stats(field_pages),
        "field_resonance_index": safe_stats(field_fri),
        "delta_phi_field": safe_stats(field_dphi),
    }

    summary["top_pages_by_glyph_count"] = sorted(
        pages,
        key=lambda p: float(p.get("num_glyph_seeds", 0)),
        reverse=True,
    )[:10]

    summary["top_glyphs_by_intensity"] = sorted(
        seeds,
        key=lambda s: float(s.get("intensity", 0.0)),
        reverse=True,
    )[:25]

    return summary

def ledger_record(summary):
    pages = summary.get("pages", {})
    glyphs = summary.get("glyph_seeds", {})
    fields = summary.get("fields", {})

    return {
        "version": VERSION,
        "timestamp_utc": summary.get("timestamp_utc", now_utc_iso()),
        "num_pages": summary.get("num_pages", 0),
        "num_fields": summary.get("num_fields", 0),
        "num_glyph_seeds": summary.get("num_glyph_seeds", 0),
        "glyphs_per_page_mean": pages.get("glyphs_per_page", {}).get("mean", 0.0),
        "glyph_intensity_mean": glyphs.get("intensity", {}).get("mean", 0.0),
        "field_spread_mean": fields.get("num_pages", {}).get("mean", 0.0),
    }

# ─────────────────────────────
# Main
# ─────────────────────────────

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    data_dir   = os.path.join(root, "data")
    meaning_v6_0 = os.path.join(data_dir, "meaning_v6_0")
    meaning_v6_1 = os.path.join(data_dir, "meaning_v6_1")

    glyph_field_path = os.path.join(meaning_v6_0, "hybrid_glyph_field_v6_0.json")

    out_expansion_path = os.path.join(meaning_v6_1, "hybrid_glyph_expansion_v6_1.json")
    out_summary_path   = os.path.join(meaning_v6_1, "hybrid_glyph_expansion_summary_v6_1.json")
    out_ledger_path    = os.path.join(meaning_v6_1, "hybrid_glyph_expansion_ledger_v6_1.jsonl")

    glyph_field_obj = load_glyph_field(glyph_field_path)

    # External image signature only — numeric processing happens elsewhere.
    glyph_seed_meta = {
        "mode": "external_image_signature",
        "tag": "voynich_hybrid_seed_v6_1",
        "source_image_hint": "voynich_glyph_seed_v6_1.png",
        "note": "External image acts as symbolic glyph seed; no direct pixel data used here.",
    }

    expansion_obj = build_glyph_expansion(glyph_field_obj, glyph_seed_meta)
    summary = summarize_expansion(expansion_obj)
    led = ledger_record(summary)

    save_json(out_expansion_path, expansion_obj)
    save_json(out_summary_path, summary)
    append_jsonl(out_ledger_path, led)

    print("Hybrid glyph expansion v6.1     ->", out_expansion_path)
    print("Hybrid glyph summary v6.1       ->", out_summary_path)
    print("Hybrid glyph ledger v6.1        ->", out_ledger_path)

if __name__ == "__main__":
    main()
