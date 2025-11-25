#!/usr/bin/env python
# -*- coding: utf-8 -*-
# VOYNICH OS — Hybrid Corpus v1.0 (EVA + Takahashi) Engine
# Auto-written by All-One PS (v6.0)

import os
import json
import datetime

VERSION = "v1_0"

def now_utc_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_text_lines(path):
    if not os.path.isfile(path):
        return []
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line:
                lines.append(line)
    return lines

def parse_corpus_lines(lines, default_page="GLOBAL_PAGE"):
    """Parse lines of form 'PAGE:: text...' or just 'text...'."""
    pages = {}
    for line in lines:
        if "::" in line:
            prefix, text = line.split("::", 1)
            page_id = prefix.strip()
            content = text.strip()
        else:
            page_id = default_page
            content = line
        if not content:
            continue
        if page_id not in pages:
            pages[page_id] = []
        pages[page_id].append(content)
    return pages

def stats_for_pages(page_map):
    total_lines = 0
    total_tokens = 0
    page_stats = {}
    for pid, lines in page_map.items():
        num_lines = len(lines)
        tokens = []
        for ln in lines:
            tokens.extend(ln.split())
        num_tokens = len(tokens)
        page_stats[pid] = {
            "num_lines": num_lines,
            "num_tokens": num_tokens,
        }
        total_lines += num_lines
        total_tokens += num_tokens
    return {
        "total_pages": len(page_map),
        "total_lines": total_lines,
        "total_tokens": total_tokens,
        "pages": page_stats,
    }

def merge_page_stats(eva_stats, taka_stats):
    eva_pages = eva_stats.get("pages", {}) if eva_stats else {}
    taka_pages = taka_stats.get("pages", {}) if taka_stats else {}
    all_page_ids = set(eva_pages.keys()) | set(taka_pages.keys())
    merged_pages = []

    for pid in sorted(all_page_ids):
        e = eva_pages.get(pid, {"num_lines": 0, "num_tokens": 0})
        t = taka_pages.get(pid, {"num_lines": 0, "num_tokens": 0})
        merged_pages.append({
            "page_id": pid,
            "eva": {
                "num_lines": int(e.get("num_lines", 0)),
                "num_tokens": int(e.get("num_tokens", 0)),
            },
            "takahashi": {
                "num_lines": int(t.get("num_lines", 0)),
                "num_tokens": int(t.get("num_tokens", 0)),
            },
            "delta_lines": int(e.get("num_lines", 0)) - int(t.get("num_lines", 0)),
            "delta_tokens": int(e.get("num_tokens", 0)) - int(t.get("num_tokens", 0)),
        })
    return merged_pages

def summarize_global(eva_stats, taka_stats, merged_pages):
    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "sources_present": {
            "eva": bool(eva_stats),
            "takahashi": bool(taka_stats),
        },
        "num_pages_union": len(merged_pages),
    }

    if eva_stats:
        summary["eva"] = {
            "total_pages": eva_stats.get("total_pages", 0),
            "total_lines": eva_stats.get("total_lines", 0),
            "total_tokens": eva_stats.get("total_tokens", 0),
        }
    if taka_stats:
        summary["takahashi"] = {
            "total_pages": taka_stats.get("total_pages", 0),
            "total_lines": taka_stats.get("total_lines", 0),
            "total_tokens": taka_stats.get("total_tokens", 0),
        }

    both = 0
    for p in merged_pages:
        e_n = p["eva"]["num_tokens"]
        t_n = p["takahashi"]["num_tokens"]
        if e_n > 0 and t_n > 0:
            both += 1
    summary["pages_with_both_sources"] = both

    return summary

def append_jsonl(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        import json
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        import json
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    corpus_dir = os.path.join(root, "data", "corpus")
    hybrid_dir = os.path.join(root, "data", "hybrid_v1_0")

    eva_path  = os.path.join(corpus_dir, "voynich_eva.txt")
    taka_path = os.path.join(corpus_dir, "voynich_takahashi.txt")

    hybrid_corpus_path  = os.path.join(hybrid_dir, "hybrid_corpus_v1_0.json")
    hybrid_summary_path = os.path.join(hybrid_dir, "hybrid_summary_v1_0.json")
    hybrid_ledger_path  = os.path.join(hybrid_dir, "hybrid_ledger_v1_0.jsonl")

    eva_lines  = load_text_lines(eva_path)
    taka_lines = load_text_lines(taka_path)

    eva_pages  = parse_corpus_lines(eva_lines,  default_page="EVA_GLOBAL") if eva_lines  else {}
    taka_pages = parse_corpus_lines(taka_lines, default_page="TAKA_GLOBAL") if taka_lines else {}

    eva_stats  = stats_for_pages(eva_pages)  if eva_pages  else None
    taka_stats = stats_for_pages(taka_pages) if taka_pages else None

    merged_pages = merge_page_stats(eva_stats or {"pages": {}},
                                    taka_stats or {"pages": {}})

    summary = summarize_global(eva_stats, taka_stats, merged_pages)

    corpus_obj = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "sources": {
            "eva": eva_stats,
            "takahashi": taka_stats,
        },
        "pages": merged_pages,
    }

    save_json(hybrid_corpus_path, corpus_obj)
    save_json(hybrid_summary_path, summary)
    append_jsonl(hybrid_ledger_path, summary)

    print("Hybrid corpus v1.0      ->", hybrid_corpus_path)
    print("Hybrid summary v1.0     ->", hybrid_summary_path)
    print("Hybrid ledger v1.0      ->", hybrid_ledger_path)
    if not eva_lines and not taka_lines:
        print("[WARN] No EVA or Takahashi corpora found. Stub summary only.")
    elif not eva_lines:
        print("[WARN] EVA corpus missing or empty.")
    elif not taka_lines:
        print("[WARN] Takahashi corpus missing or empty.")

if __name__ == "__main__":
    main()
