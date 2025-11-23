"""Voynich OS — Semantic Weather Engine v3.9

Safe, deterministic semantic weather field for Voynich OS.

Inputs
------
  • data/meaning_v3_7/atlas_graph_v3_7.json
      - combined graph of themes, clusters, folios, continuity edges
  • data/meaning_v3_7/meaning_atlas_v3_7.json
      - global atlas summary & continuity stats
  • data/meaning_v3_8/semantic_horizon_v3_8.json
      - per-folio, per-theme, per-cluster horizon metrics
  • data/meaning_v3_8/horizon_map_v3_8.json
      - global horizon distributions (continuity, pressure, density)
  • data/meaning_v3_8/horizon_intersections_v3_8.json
      - folio / cluster intersection info
  • data/meaning_v3_8/meaning_pressure_v3_8.json
      - pressure scoreboards for themes, clusters, folios

Outputs (under data/meaning_v3_9/)
----------------------------------
  • semantic_weather_v3_9.json
       - per-folio, per-theme, per-cluster weather metrics
  • weather_map_v3_9.json
       - global weather field (fronts, calm zones, extremes)
  • weather_field_v3_9.json
       - compact numeric field snapshot over folio index
  • semantic_forecast_v3_9.json
       - per-folio forecast-style summaries
  • weather_ledger_v3_9.jsonl
       - append-only ledger of v3.9 runs

All logic is:
  • Deterministic
  • Non-adaptive
  • Purely analytic (no learning, no randomness)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone


REPO_ROOT = Path(__file__).resolve().parents[1]

MEANING_V37 = REPO_ROOT / "data" / "meaning_v3_7"
MEANING_V38 = REPO_ROOT / "data" / "meaning_v3_8"
OUTDIR      = REPO_ROOT / "data" / "meaning_v3_9"

ATLAS_GRAPH      = MEANING_V37 / "atlas_graph_v3_7.json"
ATLAS_SUMMARY    = MEANING_V37 / "meaning_atlas_v3_7.json"
SEMANTIC_HORIZON = MEANING_V38 / "semantic_horizon_v3_8.json"
HORIZON_MAP      = MEANING_V38 / "horizon_map_v3_8.json"
HORIZON_INTER    = MEANING_V38 / "horizon_intersections_v3_8.json"
MEANING_PRESSURE = MEANING_V38 / "meaning_pressure_v3_8.json"

SEMANTIC_WEATHER  = OUTDIR / "semantic_weather_v3_9.json"
WEATHER_MAP       = OUTDIR / "weather_map_v3_9.json"
WEATHER_FIELD     = OUTDIR / "weather_field_v3_9.json"
SEMANTIC_FORECAST = OUTDIR / "semantic_forecast_v3_9.json"
WEATHER_LEDGER    = OUTDIR / "weather_ledger_v3_9.jsonl"


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────

def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)


def _append_ledger_entry(path: Path, entry: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(entry, sort_keys=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _safe_float(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _safe_int(x: Any) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _normalize(x: float, lo: float, hi: float) -> float:
    if hi <= lo:
        return 0.0
    return max(0.0, min(1.0, (x - lo) / (hi - lo)))


# ────────────────────────────────────────────────────────────────────
# Core extraction
# ────────────────────────────────────────────────────────────────────

def _build_folio_order(per_folio: List[Dict[str, Any]]) -> List[str]:
    """Deterministic folio ordering by lexicographic folio_id."""
    ids = [str(f.get("folio_id")) for f in per_folio if f.get("folio_id")]
    return sorted(set(ids))


def _build_folio_index(per_folio: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(f["folio_id"]): f for f in per_folio if f.get("folio_id")}


def _build_global_ranges(horizon_map: Dict[str, Any]) -> Dict[str, Tuple[float, float, float]]:
    """
    Extract min/avg/max triples for key fields from horizon_map_v3_8.
    Returns dict[field_name] = (min, avg, max).
    """
    fields = (horizon_map.get("fields") or {}) if isinstance(horizon_map, dict) else {}
    out: Dict[str, Tuple[float, float, float]] = {}
    for key, stats in fields.items():
        if not isinstance(stats, dict):
            continue
        mn = _safe_float(stats.get("min"))
        mx = _safe_float(stats.get("max"))
        av = _safe_float(stats.get("avg"))
        out[key] = (mn, av, mx)
    return out


def _build_pressure_maps(pressure: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build lookup maps from meaning_pressure_v3_8:
      - theme_pressure_map
      - cluster_pressure_map
      - folio_pressure_map
    """
    themes = pressure.get("themes", []) if isinstance(pressure, dict) else []
    clusters = pressure.get("clusters", []) if isinstance(pressure, dict) else []
    folios = pressure.get("folios", []) if isinstance(pressure, dict) else []

    theme_map = {str(t.get("theme_label")): t for t in themes if t.get("theme_label")}
    cluster_map = {str(c.get("cluster_id")): c for c in clusters if c.get("cluster_id")}
    folio_map = {str(f.get("folio_id")): f for f in folios if f.get("folio_id")}

    return {
        "themes": theme_map,
        "clusters": cluster_map,
        "folios": folio_map,
    }


def _partition_edges_by_relation(atlas_graph: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    edges_raw = atlas_graph.get("edges", []) or []
    by_rel: Dict[str, List[Dict[str, Any]]] = {}
    for e in edges_raw:
        rel = e.get("relation") or "mesh_link"
        by_rel.setdefault(rel, []).append(e)
    return by_rel


def _build_cluster_to_folios(cluster_folio_edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    m: Dict[str, List[str]] = {}
    for e in cluster_folio_edges:
        cid = str(e.get("source"))
        fid = str(e.get("target"))
        if not cid or not fid:
            continue
        m.setdefault(cid, []).append(fid)
    return m


# ────────────────────────────────────────────────────────────────────
# Weather builders
# ────────────────────────────────────────────────────────────────────

def _compute_folio_gradients(
    folio_order: List[str],
    folio_index: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """
    Compute simple 1D gradients along the folio ordering for:
      - continuity_avg
      - local_theme_pressure
      - local_motif_density
    """
    gradients: Dict[str, Dict[str, float]] = {}

    # Build raw series
    cont_series = []
    press_series = []
    dens_series = []
    for fid in folio_order:
        f = folio_index.get(fid, {})
        cont = _safe_float(f.get("continuity_avg"))
        press = _safe_float(f.get("local_theme_pressure"))
        dens = _safe_float(f.get("local_motif_density"))
        cont_series.append(cont)
        press_series.append(press)
        dens_series.append(dens)

    n = len(folio_order)
    if n == 0:
        return {}

    for i, fid in enumerate(folio_order):
        # Neighbour-based gradient (central difference where possible)
        if n == 1:
            cont_grad = 0.0
            press_grad = 0.0
            dens_grad = 0.0
        elif i == 0:
            cont_grad = cont_series[i + 1] - cont_series[i]
            press_grad = press_series[i + 1] - press_series[i]
            dens_grad = dens_series[i + 1] - dens_series[i]
        elif i == n - 1:
            cont_grad = cont_series[i] - cont_series[i - 1]
            press_grad = press_series[i] - press_series[i - 1]
            dens_grad = dens_series[i] - dens_series[i - 1]
        else:
            cont_grad = 0.5 * (cont_series[i + 1] - cont_series[i - 1])
            press_grad = 0.5 * (press_series[i + 1] - press_series[i - 1])
            dens_grad = 0.5 * (dens_series[i + 1] - dens_series[i - 1])

        gradients[fid] = {
            "continuity_gradient": cont_grad,
            "pressure_gradient": press_grad,
            "density_gradient": dens_grad,
        }

    return gradients


def build_semantic_weather(
    semantic_horizon: Dict[str, Any],
    horizon_map: Dict[str, Any],
    horizon_intersections: Dict[str, Any],
    meaning_pressure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the core semantic weather structure:
      - per_folio weather metrics
      - theme-level weather
      - cluster-level weather
    """
    per_folio_raw = semantic_horizon.get("per_folio", []) if isinstance(semantic_horizon, dict) else []
    themes_raw = semantic_horizon.get("themes", []) if isinstance(semantic_horizon, dict) else []
    clusters_raw = semantic_horizon.get("clusters", []) if isinstance(semantic_horizon, dict) else []

    folio_order = _build_folio_order(per_folio_raw)
    folio_index = _build_folio_index(per_folio_raw)
    gradients = _compute_folio_gradients(folio_order, folio_index)

    ranges = _build_global_ranges(horizon_map)
    cont_min, cont_avg, cont_max = ranges.get("continuity_avg", (0.0, 0.0, 1.0))
    press_min, press_avg, press_max = ranges.get("theme_pressure", (0.0, 0.0, 1.0))
    dens_min, dens_avg, dens_max = ranges.get("motif_density", (0.0, 0.0, 1.0))

    hot_folios = set()
    high_zone_folios = set()
    if isinstance(horizon_intersections, dict):
        for f in horizon_intersections.get("folio_intersections", []):
            fid = str(f.get("folio_id"))
            if fid:
                hot_folios.add(fid)
    # high continuity zones already flagged in semantic_horizon (is_high_continuity_zone)

    pressure_maps = _build_pressure_maps(meaning_pressure)
    theme_pressure_map = pressure_maps["themes"]
    cluster_pressure_map = pressure_maps["clusters"]
    folio_pressure_map = pressure_maps["folios"]

    # Per-folio weather
    per_folio_weather: List[Dict[str, Any]] = []
    for fid in folio_order:
        base = folio_index.get(fid, {})
        grad = gradients.get(fid, {})

        cont = _safe_float(base.get("continuity_avg"))
        press = _safe_float(base.get("local_theme_pressure"))
        dens = _safe_float(base.get("local_motif_density"))

        cont_norm = _normalize(cont, cont_min, cont_max)
        press_norm = _normalize(press, press_min, press_max)
        dens_norm = _normalize(dens, dens_min, dens_max)

        cont_grad = _safe_float(grad.get("continuity_gradient"))
        press_grad = _safe_float(grad.get("pressure_gradient"))
        dens_grad = _safe_float(grad.get("density_gradient"))

        # Simple volatility index from gradients
        volatility = min(1.0, (abs(cont_grad) + abs(press_grad)) / (abs(cont_avg) + 1e-6))

        # Storm index: strong pressure + moderate/low continuity + high volatility
        storm_index = max(0.0, press_norm * (1.0 - cont_norm) * (0.5 + 0.5 * volatility))

        # Stability index: high continuity + low volatility
        stability_index = max(0.0, cont_norm * (1.0 - 0.5 * volatility))

        # Drift index: low pressure + low continuity
        drift_index = max(0.0, (1.0 - press_norm) * (1.0 - cont_norm))

        # Category assignment (deterministic)
        if stability_index >= 0.7 and storm_index <= 0.3:
            category = "stable_band"
        elif storm_index >= 0.6:
            category = "storm_front"
        elif drift_index >= 0.5 and cont_norm <= 0.4:
            category = "drift_trough"
        else:
            category = "mixed_flow"

        # Rising / falling pressure relative to global average
        if press > press_avg * 1.1:
            pressure_trend = "rising"
        elif press < press_avg * 0.9:
            pressure_trend = "falling"
        else:
            pressure_trend = "steady"

        per_folio_weather.append(
            {
                "folio_id": fid,
                "dominant_theme": base.get("dominant_theme"),
                "dominant_score": _safe_float(base.get("dominant_score")),
                "num_clusters": _safe_int(base.get("num_clusters")),
                "num_motifs": _safe_int(base.get("num_motifs")),
                "cross_link_degree": _safe_float(base.get("cross_link_degree")),
                "continuity_avg": cont,
                "local_theme_pressure": press,
                "local_motif_density": dens,
                "continuity_norm": cont_norm,
                "pressure_norm": press_norm,
                "density_norm": dens_norm,
                "continuity_gradient": cont_grad,
                "pressure_gradient": press_grad,
                "density_gradient": dens_grad,
                "volatility_index": volatility,
                "storm_index": storm_index,
                "stability_index": stability_index,
                "drift_index": drift_index,
                "category": category,
                "pressure_trend": pressure_trend,
                "is_hot_intersection": fid in hot_folios,
                "is_high_continuity_zone": bool(base.get("is_high_continuity_zone")),
                "is_hotspot_boundary": bool(base.get("is_hotspot_boundary")),
            }
        )

    # Theme weather
    theme_weather: List[Dict[str, Any]] = []
    for t in themes_raw:
        label = str(t.get("theme_label"))
        base = t
        p = theme_pressure_map.get(label, {})

        avg_press = _safe_float(p.get("avg_theme_pressure"))
        avg_cont = _safe_float(p.get("avg_continuity"))
        num_dom = _safe_int(p.get("num_dominant_folios"))

        press_state = "neutral"
        if avg_press > press_avg * 1.1:
            press_state = "high_pressure"
        elif avg_press < press_avg * 0.9:
            press_state = "low_pressure"

        theme_weather.append(
            {
                "theme_label": label,
                "num_dominant_folios": num_dom,
                "avg_theme_pressure": avg_press,
                "avg_continuity": avg_cont,
                "hotspot_folios": _safe_int(base.get("hotspot_folios")),
                "high_zone_folios": _safe_int(base.get("high_zone_folios")),
                "pressure_state": press_state,
            }
        )

    # Cluster weather
    cluster_weather: List[Dict[str, Any]] = []
    for c in clusters_raw:
        cid = str(c.get("cluster_id"))
        base = c
        p = cluster_pressure_map.get(cid, {})

        nf = _safe_int(base.get("num_folios"))
        ca = _safe_float(base.get("continuity_avg"))
        td = _safe_int(base.get("theme_diversity"))
        pressure = _safe_float(p.get("pressure")) if p else nf * ca

        cluster_weather.append(
            {
                "cluster_id": cid,
                "num_folios": nf,
                "continuity_avg": ca,
                "theme_diversity": td,
                "themes": base.get("themes", []),
                "pressure": pressure,
            }
        )

    return {
        "meta": {
            "version": "3.9",
            "description": "Semantic weather metrics across folios, themes, and clusters.",
        },
        "per_folio": per_folio_weather,
        "themes": theme_weather,
        "clusters": cluster_weather,
    }


def build_weather_map(semantic_weather: Dict[str, Any]) -> Dict[str, Any]:
    """Build global weather map: fronts, calm zones, extremes."""
    per_folio = semantic_weather.get("per_folio", [])

    if not per_folio:
        return {
            "meta": {
                "version": "3.9",
                "description": "Empty weather map (no folios).",
            },
            "fronts": [],
            "calm_zones": [],
            "extremes": {},
        }

    # Sort by storm_index, stability_index, pressure_norm
    storms = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("storm_index")),
        reverse=True,
    )
    calm = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("stability_index")),
        reverse=True,
    )
    high_pressure = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("pressure_norm")),
        reverse=True,
    )
    low_pressure = sorted(
        per_folio,
        key=lambda f: _safe_float(f.get("pressure_norm")),
    )

    fronts = [
        {
            "folio_id": f.get("folio_id"),
            "storm_index": _safe_float(f.get("storm_index")),
            "pressure_trend": f.get("pressure_trend"),
            "category": f.get("category"),
        }
        for f in storms[:20]
    ]

    calm_zones = [
        {
            "folio_id": f.get("folio_id"),
            "stability_index": _safe_float(f.get("stability_index")),
            "category": f.get("category"),
        }
        for f in calm[:20]
    ]

    extremes = {
        "high_pressure_folios": [
            {"folio_id": f.get("folio_id"), "pressure_norm": _safe_float(f.get("pressure_norm"))}
            for f in high_pressure[:20]
        ],
        "low_pressure_folios": [
            {"folio_id": f.get("folio_id"), "pressure_norm": _safe_float(f.get("pressure_norm"))}
            for f in low_pressure[:20]
        ],
    }

    return {
        "meta": {
            "version": "3.9",
            "description": "Global semantic weather map (fronts, calm zones, extremes).",
        },
        "fronts": fronts,
        "calm_zones": calm_zones,
        "extremes": extremes,
    }


def build_weather_field(
    semantic_weather: Dict[str, Any],
) -> Dict[str, Any]:
    """Compact numeric field snapshot over folio index."""
    per_folio = semantic_weather.get("per_folio", [])
    if not per_folio:
        return {
            "meta": {
                "version": "3.9",
                "description": "Empty weather field (no folios).",
            },
            "folio_ids": [],
            "stability": [],
            "storm": [],
            "pressure": [],
        }

    folio_ids = [f.get("folio_id") for f in per_folio]
    stability = [_safe_float(f.get("stability_index")) for f in per_folio]
    storm = [_safe_float(f.get("storm_index")) for f in per_folio]
    pressure = [_safe_float(f.get("pressure_norm")) for f in per_folio]

    return {
        "meta": {
            "version": "3.9",
            "description": "Numeric semantic weather field over ordered folios.",
        },
        "folio_ids": folio_ids,
        "stability_index": stability,
        "storm_index": storm,
        "pressure_norm": pressure,
    }


def build_semantic_forecast(semantic_weather: Dict[str, Any]) -> Dict[str, Any]:
    """Build per-folio forecast-style summaries (deterministic, analytic)."""
    per_folio = semantic_weather.get("per_folio", [])
    forecasts: List[Dict[str, Any]] = []

    for f in per_folio:
        fid = f.get("folio_id")
        if not fid:
            continue

        cat = f.get("category")
        storm = _safe_float(f.get("storm_index"))
        stab = _safe_float(f.get("stability_index"))
        drift = _safe_float(f.get("drift_index"))
        pressure_trend = f.get("pressure_trend")

        if cat == "storm_front":
            summary = "Unstable semantic weather with strong theme shear."
        elif cat == "stable_band":
            summary = "Stable meaning band with smooth thematic flow."
        elif cat == "drift_trough":
            summary = "Low-pressure, low-continuity region; meaning may be shifting."
        else:
            summary = "Mixed-flow region with moderate semantic variation."

        forecasts.append(
            {
                "folio_id": fid,
                "category": cat,
                "summary": summary,
                "storm_index": storm,
                "stability_index": stab,
                "drift_index": drift,
                "pressure_trend": pressure_trend,
                "dominant_theme": f.get("dominant_theme"),
            }
        )

    return {
        "meta": {
            "version": "3.9",
            "description": "Per-folio semantic weather forecast (analytic).",
        },
        "folios": forecasts,
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v3_9_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    atlas_graph = _load_json(ATLAS_GRAPH)
    atlas_summary = _load_json(ATLAS_SUMMARY)  # not heavily used yet, but kept for future hooks
    semantic_horizon = _load_json(SEMANTIC_HORIZON)
    horizon_map = _load_json(HORIZON_MAP)
    try:
        horizon_inter = _load_json(HORIZON_INTER)
    except FileNotFoundError:
        horizon_inter = {}
    meaning_pressure = _load_json(MEANING_PRESSURE)

    semantic_weather = build_semantic_weather(
        semantic_horizon=semantic_horizon,
        horizon_map=horizon_map,
        horizon_intersections=horizon_inter,
        meaning_pressure=meaning_pressure,
    )
    weather_map = build_weather_map(semantic_weather)
    weather_field = build_weather_field(semantic_weather)
    semantic_forecast = build_semantic_forecast(semantic_weather)

    _write_json(SEMANTIC_WEATHER, semantic_weather)
    _write_json(WEATHER_MAP, weather_map)
    _write_json(WEATHER_FIELD, weather_field)
    _write_json(SEMANTIC_FORECAST, semantic_forecast)

    # Ledger entry
    per_folio = semantic_weather.get("per_folio", [])
    themes = semantic_weather.get("themes", [])
    clusters = semantic_weather.get("clusters", [])

    ts = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": ts,
        "version": "3.9",
        "num_folios": len(per_folio),
        "num_themes": len(themes),
        "num_clusters": len(clusters),
    }
    _append_ledger_entry(WEATHER_LEDGER, entry)

    print(f"Semantic weather   → {SEMANTIC_WEATHER}")
    print(f"Weather map        → {WEATHER_MAP}")
    print(f"Weather field      → {WEATHER_FIELD}")
    print(f"Semantic forecast  → {SEMANTIC_FORECAST}")
    print(f"Ledger append      → {WEATHER_LEDGER}")


if __name__ == "__main__":
    run_v3_9_pipeline()
