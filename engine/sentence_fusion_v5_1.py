"""
Voynich OS v5.1 — Sentence Fusion Engine
Law: Vector fusion → semantic alignment → proto-sentence generation
"""

import json, pathlib, datetime, math, statistics

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Inputs
V49_MAP     = DATA / "meaning_v4_9" / "semantic_attractor_map_v4_9.json"
V50_SURFACE = DATA / "meaning_v5_0" / "translation_surface_v5_0.json"

OUT = DATA / "meaning_v5_1"
OUT.mkdir(parents=True, exist_ok=True)

SENT_PATH   = OUT / "fusion_sentences_v5_1.json"
MAP_PATH    = OUT / "fusion_map_v5_1.json"
CLU_PATH    = OUT / "fusion_clusters_v5_1.json"
SUM_PATH    = OUT / "fusion_summary_v5_1.json"
LEDGER_PATH = OUT / "fusion_ledger_v5_1.jsonl"

def safe_load(path, default=None):
    if default is None:
        default = {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def fuse_fragments(surface):
    """Fuse proto-translation units into proto-sentences."""
    units = surface.get("units", [])
    fused = []
    window = []

    for u in units:
        token = u.get("token", "")
        window.append(token)

        if len(window) >= 5:
            fused.append(" ".join(window))
            window = []

    if window:
        fused.append(" ".join(window))

    return fused

def build_cluster_map(sentences):
    clusters = {}
    for s in sentences:
        key = str(len(s.split()))
        clusters.setdefault(key, []).append(s)
    return clusters

def run():
    timestamp = datetime.datetime.utcnow().isoformat()

    v49 = safe_load(V49_MAP, {})
    v50 = safe_load(V50_SURFACE, {})

    sentences = fuse_fragments(v50)
    cluster_map = build_cluster_map(sentences)

    summary = {
        "version": "5.1",
        "timestamp": timestamp,
        "num_sentences": len(sentences),
        "avg_length": statistics.mean([len(s.split()) for s in sentences]) if sentences else 0,
        "notes": "v5.1 fused semantic units into proto-sentences."
    }

    json.dump({"sentences": sentences}, SENT_PATH.open("w", encoding="utf-8"), indent=2)
    json.dump(cluster_map, CLU_PATH.open("w", encoding="utf-8"), indent=2)
    json.dump({"clusters": list(cluster_map.keys())}, MAP_PATH.open("w", encoding="utf-8"), indent=2)
    json.dump(summary, SUM_PATH.open("w", encoding="utf-8"), indent=2)

    with LEDGER_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")

    print("Sentences →", SENT_PATH)
    print("Clusters  →", CLU_PATH)
    print("Map       →", MAP_PATH)
    print("Summary   →", SUM_PATH)
    print("Ledger    →", LEDGER_PATH)

if __name__ == "__main__":
    run()
