"""
Voynich OS — Ultra Codex Resonance Engine v4.0

SAFE, deterministic resonance computation.
NO Codex laws, NO glyph logic, NO adaptive learning.
All calculations remain structural + numeric only.

Inputs:
  • data/meaning_v3_9/semantic_weather_v3_9.json
  • data/meaning_v3_8/semantic_horizon_v3_8.json
  • data/meaning_v3_6/meaning_flow_v3_6.json
  • data/meaning_v3_7/atlas_graph_v3_7.json
  • data/meaning_v3_5/meaning_index_v3_5.json

Outputs:
  • resonance_map_v4_0.json
  • resonance_field_v4_0.json
  • resonance_clusters_v4_0.json
  • resonance_stability_v4_0.json
  • resonance_ledger_v4_0.jsonl
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]
M39 = REPO / "data" / "meaning_v3_9"
M38 = REPO / "data" / "meaning_v3_8"
M36 = REPO / "data" / "meaning_v3_6"
M37 = REPO / "data" / "meaning_v3_7"
M35 = REPO / "data" / "meaning_v3_5"
OUT = REPO / "data" / "meaning_v4_0"

WEATHER   = M39 / "semantic_weather_v3_9.json"
HORIZON   = M38 / "semantic_horizon_v3_8.json"
FLOW      = M36 / "meaning_flow_v3_6.json"
ATLAS     = M37 / "atlas_graph_v3_7.json"
INDEX     = M35 / "meaning_index_v3_5.json"

OUT_MAP      = OUT / "resonance_map_v4_0.json"
OUT_FIELD    = OUT / "resonance_field_v4_0.json"
OUT_CLUSTERS = OUT / "resonance_clusters_v4_0.json"
OUT_STAB     = OUT / "resonance_stability_v4_0.json"
OUT_LEDGER   = OUT / "resonance_ledger_v4_0.jsonl"


def load(path: Path):
    if not path.exists():
        raise FileNotFoundError(str(path))
    return json.load(path.open("r", encoding="utf8"))


def write(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def append_ledger(path: Path, entry: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf8") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


# ───────────────────────────────────────────────────────────────
# Resonance computation (SAFE numeric-only)
# ───────────────────────────────────────────────────────────────
def safe_float(x):
    try:
        return float(x)
    except:
        return 0.0


def build_resonance_map(weather, horizon):
    folios = weather.get("per_folio", [])
    out = []
    for f in folios:
        cid = f.get("folio_id")
        cont = safe_float(f.get("continuity_avg"))
        storm = safe_float(f.get("storm_index"))
        stab = safe_float(f.get("stability_index"))
        press = safe_float(f.get("pressure_norm"))

        # SAFE "resonance proxy" (not Codex ΔΦ)
        resonance = (cont * 0.6) + (press * 0.3) - (storm * 0.2)
        if resonance < 0: resonance = 0.0

        out.append({
            "folio_id": cid,
            "continuity": cont,
            "pressure": press,
            "storm": storm,
            "stability": stab,
            "resonance_index": resonance,
        })

    out.sort(key=lambda x: x["resonance_index"], reverse=True)
    return out


def build_resonance_field(resonance_map):
    return {
        "folio_ids": [r["folio_id"] for r in resonance_map],
        "resonance_index": [r["resonance_index"] for r in resonance_map],
        "continuity": [r["continuity"] for r in resonance_map],
    }


def build_cluster_resonance(atlas_graph, resonance_map):
    rmap = {r["folio_id"]: r["resonance_index"] for r in resonance_map}
    edges = atlas_graph.get("edges", [])
    clusters = {}

    for e in edges:
        if e.get("relation") == "appears_in_folio":
            cid = str(e.get("source"))
            fid = str(e.get("target"))
            clusters.setdefault(cid, []).append(rmap.get(fid, 0.0))

    out = []
    for cid, vals in clusters.items():
        if vals:
            avg = sum(vals)/len(vals)
        else:
            avg = 0.0
        out.append({"cluster_id": cid, "avg_resonance": avg})

    out.sort(key=lambda x: x["avg_resonance"], reverse=True)
    return out


def build_stability_map(resonance_map):
    return {
        "high_resonance": [r for r in resonance_map if r["resonance_index"] >= 0.5],
        "low_resonance":  [r for r in resonance_map if r["resonance_index"] < 0.15],
    }


def run_v4():
    OUT.mkdir(parents=True, exist_ok=True)

    weather = load(WEATHER)
    horizon = load(HORIZON)
    try:
        flow = load(FLOW)
    except:
        flow = {}
    atlas = load(ATLAS)
    idx   = load(INDEX)

    resonance_map = build_resonance_map(weather, horizon)
    resonance_field = build_resonance_field(resonance_map)
    cluster_res = build_cluster_resonance(atlas, resonance_map)
    stab = build_stability_map(resonance_map)

    write(OUT_MAP, resonance_map)
    write(OUT_FIELD, resonance_field)
    write(OUT_CLUSTERS, cluster_res)
    write(OUT_STAB, stab)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "4.0",
        "num_folios": len(resonance_map),
        "num_clusters": len(cluster_res)
    }
    append_ledger(OUT_LEDGER, entry)

    print("Resonance map     →", OUT_MAP)
    print("Resonance field   →", OUT_FIELD)
    print("Cluster resonance →", OUT_CLUSTERS)
    print("Stability map     →", OUT_STAB)
    print("Ledger            →", OUT_LEDGER)


if __name__ == "__main__":
    run_v4()
