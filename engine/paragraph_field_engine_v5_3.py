#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 𓂀  VOYNICH OS v5.3 — Paragraph Field Engine (Auto-Generated All-One PS)

import json, math, os, statistics, datetime
from collections import defaultdict

VERSION = "v5_3"

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

def normalize_bonds(raw):
    out = []
    if not isinstance(raw, list):
        return out
    for e in raw:
        if not isinstance(e, dict):
            continue
        src = e.get("source") or e.get("sentence_a")
        dst = e.get("target") or e.get("sentence_b")
        w   = e.get("weight") or e.get("score") or 1.0
        if src and dst:
            out.append((str(src), str(dst), float(w)))
    return out

def normalize_clusters(raw):
    clusters = {}
    if isinstance(raw, dict):
        for k,v in raw.items():
            clusters[str(k)] = [str(x) for x in v]
        return clusters
    if isinstance(raw, list):
        for i,e in enumerate(raw):
            if isinstance(e, dict):
                fid = e.get("cluster_id") or e.get("id") or f"cluster_{i}"
                for key in ("sentences","members","items"):
                    if key in e:
                        clusters[str(fid)] = [str(x) for x in e[key]]
                        break
            if isinstance(e, list):
                clusters[f"cluster_{i}"] = [str(x) for x in e]
        return clusters
    return clusters

def compute_fields(bonds, clusters):
    sentence_field = defaultdict(list)
    for fid, sids in clusters.items():
        for s in sids:
            sentence_field[s].append(fid)

    stats = {fid: {"intra_w":0,"intra_c":0,"cross_w":0,"cross_c":0}
             for fid in clusters}

    edges = defaultdict(float)

    for src, dst, w in bonds:
        fs = sentence_field.get(src, [])
        fd = sentence_field.get(dst, [])
        if not fs and not fd:
            continue

        for a in fs or [None]:
            for b in fd or [None]:
                if a and a==b:
                    stats[a]["intra_w"] += w
                    stats[a]["intra_c"] += 1
                involved = set()
                if a: involved.add(a)
                if b: involved.add(b)
                if len(involved)==1:
                    x = next(iter(involved))
                    stats[x]["cross_w"] += w
                    stats[x]["cross_c"] += 1
                if len(involved)==2:
                    p = tuple(sorted(involved))
                    edges[p] += w

    fields = []
    final_edges = []

    for fid, sids in clusters.items():
        st = stats[fid]
        intra = st["intra_w"]
        cross = st["cross_w"]
        total = intra + cross if (intra+cross)>0 else 1
        dphi = (cross/total) - (intra/total)

        fri = math.log1p(max(intra,0)) / (1 + abs(dphi))

        fields.append({
            "field_id": fid,
            "version": VERSION,
            "sentence_ids": sids,
            "metrics": {
                "num_sentences": len(sids),
                "intra_weight": intra,
                "cross_weight": cross,
                "intra_ratio": intra/total,
                "cross_ratio": cross/total,
                "delta_phi_field": dphi,
                "field_resonance_index": fri
            }
        })

    for (a,b), w in edges.items():
        final_edges.append({
            "field_a": a, "field_b": b,
            "weight": float(w), "version": VERSION
        })

    return fields, final_edges

def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    v52 = os.path.join(root,"data","meaning_v5_2")
    v53 = os.path.join(root,"data","meaning_v5_3")

    bonds_p = os.path.join(v52,"semantic_bonds_v5_2.json")
    clust_p = os.path.join(v52,"bond_clusters_v5_2.json")

    fields_p  = os.path.join(v53,"paragraph_fields_v5_3.json")
    graph_p   = os.path.join(v53,"field_graph_v5_3.json")
    summary_p = os.path.join(v53,"field_summary_v5_3.json")
    ledger_p  = os.path.join(v53,"bonding_ledger_v5_3.jsonl")

    bonds = normalize_bonds(load_json(bonds_p, []))
    clusters = normalize_clusters(load_json(clust_p, {}))

    fields, edges = compute_fields(bonds, clusters)
    summary = {
        "version": VERSION,
        "timestamp_utc": now_utc_iso(),
        "num_fields": len(fields)
    }

    save_json(fields_p,  {"fields":fields, "version":VERSION})
    save_json(graph_p,   {"edges":edges,   "version":VERSION})
    save_json(summary_p, summary)
    append_jsonl(ledger_p, summary)

    print("Paragraph fields v5.3     →", fields_p)
    print("Field graph v5.3          →", graph_p)
    print("Field summary v5.3        →", summary_p)
    print("Bonding ledger v5.3 append→", ledger_p)

if __name__=="__main__":
    main()
