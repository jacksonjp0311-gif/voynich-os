"""Voynich OS — Semantic Flow Engine v4.2

Safe, deterministic semantic flow field for Voynich OS.

Inputs
------
  • data/meaning_v3_9/semantic_weather_v3_9.json
      - per-folio weather metrics (stability, storm, pressure, volatility)
  • data/meaning_v3_9/weather_field_v3_9.json
      - compact per-folio arrays (stability, storm, pressure)
  • data/meaning_v4_0/semantic_vortex_v4_0.json
      - per-folio vortex metrics (vorticity, shear, rotation bands)
  • data/meaning_v4_0/vortex_bands_v4_0.json
      - banded vortex regime map
  • data/meaning_v4_1/semantic_isobars_v4_1.json
      - per-folio pressure banding + isobar class
  • data/meaning_v4_1/isobar_bands_v4_1.json
      - banded isobar values / pressure levels
  • data/meaning_v4_1/isobar_zones_v4_1.json
      - stable belts, front lines, drift basins

Outputs (under data/meaning_v4_2/)
----------------------------------
  • semantic_flow_v4_2.json
       - per-folio semantic flow vectors + regime classification
  • flow_field_v4_2.json
       - compact numeric flow field over ordered folios
  • flow_segments_v4_2.json
       - contiguous high-flow and low-flow bands
  • flow_topology_v4_2.json
       - simple flow topology (sources, sinks, shear lines)
  • flow_ledger_v4_2.jsonl
       - append-only ledger of v4.2 runs

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

MEANING_V39 = REPO_ROOT / "data" / "meaning_v3_9"
MEANING_V40 = REPO_ROOT / "data" / "meaning_v4_0"
MEANING_V41 = REPO_ROOT / "data" / "meaning_v4_1"
OUTDIR      = REPO_ROOT / "data" / "meaning_v4_2"

SEMANTIC_WEATHER  = MEANING_V39 / "semantic_weather_v3_9.json"
WEATHER_FIELD     = MEANING_V39 / "weather_field_v3_9.json"
SEMANTIC_VORTEX   = MEANING_V40 / "semantic_vortex_v4_0.json"
VORTEX_BANDS      = MEANING_V40 / "vortex_bands_v4_0.json"
SEMANTIC_ISOBARS  = MEANING_V41 / "semantic_isobars_v4_1.json"
ISOBAR_BANDS      = MEANING_V41 / "isobar_bands_v4_1.json"
ISOBAR_ZONES      = MEANING_V41 / "isobar_zones_v4_1.json"

SEMANTIC_FLOW   = OUTDIR / "semantic_flow_v4_2.json"
FLOW_FIELD      = OUTDIR / "flow_field_v4_2.json"
FLOW_SEGMENTS   = OUTDIR / "flow_segments_v4_2.json"
FLOW_TOPOLOGY   = OUTDIR / "flow_topology_v4_2.json"
FLOW_LEDGER     = OUTDIR / "flow_ledger_v4_2.jsonl"


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

def _build_folio_order_from_weather_field(weather_field: Dict[str, Any],
                                          weather_per_folio: List[Dict[str, Any]]) -> List[str]:
    """Prefer WEATHER_FIELD folio_ids; fall back to sorted per_folio ids."""
    ids = []
    if isinstance(weather_field, dict):
        ids = [str(fid) for fid in weather_field.get("folio_ids", []) if fid]
    if not ids:
        ids = [str(f.get("folio_id")) for f in weather_per_folio if f.get("folio_id")]
    return sorted(set(ids))


def _index_by_folio(per_folio: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {str(f["folio_id"]): f for f in per_folio if f.get("folio_id")}


def _extract_weather_maps(semantic_weather: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    per_folio = semantic_weather.get("per_folio", []) if isinstance(semantic_weather, dict) else []
    return _index_by_folio(per_folio)


def _extract_vortex_maps(semantic_vortex: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    per_folio = semantic_vortex.get("per_folio", []) if isinstance(semantic_vortex, dict) else []
    return _index_by_folio(per_folio)


def _extract_isobar_maps(semantic_isobars: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    per_folio = semantic_isobars.get("per_folio", []) if isinstance(semantic_isobars, dict) else []
    return _index_by_folio(per_folio)


# ────────────────────────────────────────────────────────────────────
# Gradient + flow helpers
# ────────────────────────────────────────────────────────────────────

def _compute_gradients_series(folio_order: List[str],
                              scalar_series: List[float]) -> List[float]:
    """1D central-difference gradient over a scalar field along folio_order."""
    n = len(folio_order)
    if n == 0:
        return []
    if len(scalar_series) != n:
        # Simple safety: truncate or pad with zeros
        if len(scalar_series) > n:
            scalar_series = scalar_series[:n]
        else:
            scalar_series = scalar_series + [0.0] * (n - len(scalar_series))

    grads: List[float] = []
    for i in range(n):
        if n == 1:
            g = 0.0
        elif i == 0:
            g = scalar_series[i + 1] - scalar_series[i]
        elif i == n - 1:
            g = scalar_series[i] - scalar_series[i - 1]
        else:
            g = 0.5 * (scalar_series[i + 1] - scalar_series[i - 1])
        grads.append(g)
    return grads


def _categorize_flow(stability_norm: float,
                     storm_norm: float,
                     vorticity_norm: float,
                     pressure_grad_norm: float) -> str:
    """
    Deterministic classification of flow regime.
    """
    # Jet streams: high storm, moderate-high vorticity, strong gradient
    if storm_norm >= 0.7 and pressure_grad_norm >= 0.5:
        return "jet_stream"
    # Laminar bands: high stability, low storm, low gradient
    if stability_norm >= 0.7 and storm_norm <= 0.3 and pressure_grad_norm <= 0.3:
        return "laminar_band"
    # Shear flow: moderate-high vorticity and gradient
    if vorticity_norm >= 0.5 and pressure_grad_norm >= 0.4:
        return "shear_flow"
    # Stagnation: low storm, low gradient, low pressure norm
    if storm_norm <= 0.2 and pressure_grad_norm <= 0.2:
        return "stagnation_zone"
    # Recirculation: high vorticity but moderate-low gradient
    if vorticity_norm >= 0.6 and pressure_grad_norm <= 0.4:
        return "recirculation_cell"
    # Default
    return "mixed_flow"


# ────────────────────────────────────────────────────────────────────
# Flow builders
# ────────────────────────────────────────────────────────────────────

def build_semantic_flow(
    semantic_weather: Dict[str, Any],
    weather_field: Dict[str, Any],
    semantic_vortex: Dict[str, Any],
    semantic_isobars: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the core semantic flow structure:
      - per-folio flow vectors + regime classification
      - aggregate flow metrics
    """
    weather_per_folio = semantic_weather.get("per_folio", []) if isinstance(semantic_weather, dict) else []
    weather_map = _extract_weather_maps(semantic_weather)
    vortex_map = _extract_vortex_maps(semantic_vortex)
    isobar_map = _extract_isobar_maps(semantic_isobars)

    folio_order = _build_folio_order_from_weather_field(weather_field, weather_per_folio)

    # Build core scalar series from weather_field if present, else from semantic_weather
    if isinstance(weather_field, dict) and weather_field.get("folio_ids"):
        stability_series = [ _safe_float(x) for x in weather_field.get("stability_index", []) ]
        storm_series     = [ _safe_float(x) for x in weather_field.get("storm_index", []) ]
        pressure_series  = [ _safe_float(x) for x in weather_field.get("pressure_norm", []) ]
    else:
        # fallback: derive from weather_map
        stability_series = []
        storm_series = []
        pressure_series = []
        for fid in folio_order:
            base = weather_map.get(fid, {})
            stability_series.append(_safe_float(base.get("stability_index")))
            storm_series.append(_safe_float(base.get("storm_index")))
            pressure_series.append(_safe_float(base.get("pressure_norm")))

    n = len(folio_order)
    if not n:
        return {
            "meta": {
                "version": "4.2",
                "description": "Semantic flow structure (empty – no folios).",
            },
            "per_folio": [],
            "stats": {},
        }

    # Gradients for pressure (and optionally stability)
    pressure_grad = _compute_gradients_series(folio_order, pressure_series)
    stability_grad = _compute_gradients_series(folio_order, stability_series)

    # Simple normalization ranges from series
    p_min, p_max = min(pressure_series), max(pressure_series)
    s_min, s_max = min(stability_series), max(stability_series)
    storm_min, storm_max = min(storm_series), max(storm_series)

    # Build per-folio flow
    per_folio_flow: List[Dict[str, Any]] = []
    speeds: List[float] = []
    cats: Dict[str, int] = {}

    for i, fid in enumerate(folio_order):
        w = weather_map.get(fid, {})
        v = vortex_map.get(fid, {})
        iso = isobar_map.get(fid, {})

        stability = _safe_float(w.get("stability_index"))
        storm = _safe_float(w.get("storm_index"))
        pressure_norm = _safe_float(w.get("pressure_norm"))

        # Fallback to series if needed
        if stability == 0.0 and i < len(stability_series):
            stability = stability_series[i]
        if storm == 0.0 and i < len(storm_series):
            storm = storm_series[i]
        if pressure_norm == 0.0 and i < len(pressure_series):
            pressure_norm = pressure_series[i]

        p_grad = pressure_grad[i] if i < len(pressure_grad) else 0.0
        s_grad = stability_grad[i] if i < len(stability_grad) else 0.0

        vorticity = _safe_float(v.get("vorticity_index") or v.get("vortex_strength"))
        shear = _safe_float(v.get("shear_index"))

        # Normalize core components
        stability_norm = _normalize(stability, s_min, s_max) if s_max > s_min else 0.0
        storm_norm = _normalize(storm, storm_min, storm_max) if storm_max > storm_min else 0.0
        vorticity_norm = _normalize(abs(vorticity), 0.0, max(abs(vorticity), 1.0))
        # gradient norm scaled by max magnitude
        max_p_grad = max(abs(g) for g in pressure_grad) if pressure_grad else 1.0
        pressure_grad_norm = _normalize(abs(p_grad), 0.0, max_p_grad)

        # Flow "speed": combination of storm, vorticity, gradient
        speed = (0.4 * storm_norm) + (0.3 * vorticity_norm) + (0.3 * pressure_grad_norm)

        # Direction sign: positive for rising pressure / stable, negative for falling / unstable
        direction_scalar = p_grad - s_grad
        direction = "neutral"
        if direction_scalar > 0.0:
            direction = "rising_pressure_flow"
        elif direction_scalar < 0.0:
            direction = "falling_pressure_flow"

        category = _categorize_flow(
            stability_norm=stability_norm,
            storm_norm=storm_norm,
            vorticity_norm=vorticity_norm,
            pressure_grad_norm=pressure_grad_norm,
        )
        cats[category] = cats.get(category, 0) + 1

        isobar_class = iso.get("isobar_class") or iso.get("isobar_category") or "UNKNOWN"
        zone_label = iso.get("zone_label") or iso.get("zone_type") or ""

        rec = {
            "folio_id": fid,
            "dominant_theme": w.get("dominant_theme"),
            "stability_index": stability,
            "storm_index": storm,
            "pressure_norm": pressure_norm,
            "vorticity_index": vorticity,
            "shear_index": shear,
            "pressure_gradient": p_grad,
            "stability_gradient": s_grad,
            "flow_speed": speed,
            "flow_direction": direction,
            "flow_category": category,
            "isobar_class": isobar_class,
            "isobar_zone": zone_label,
            "is_hot_intersection": bool(w.get("is_hot_intersection")),
            "is_high_continuity_zone": bool(w.get("is_high_continuity_zone")),
            "is_hotspot_boundary": bool(w.get("is_hotspot_boundary")),
        }
        per_folio_flow.append(rec)
        speeds.append(speed)

    stats = {
        "num_folios": n,
        "speed_min": min(speeds) if speeds else 0.0,
        "speed_max": max(speeds) if speeds else 0.0,
        "speed_avg": (sum(speeds) / float(len(speeds))) if speeds else 0.0,
        "categories": cats,
    }

    return {
        "meta": {
            "version": "4.2",
            "description": "Semantic flow vectors + regimes per folio.",
        },
        "per_folio": per_folio_flow,
        "stats": stats,
    }


def build_flow_field(semantic_flow: Dict[str, Any]) -> Dict[str, Any]:
    """Compact numeric flow field snapshot over folio index."""
    per_folio = semantic_flow.get("per_folio", []) if isinstance(semantic_flow, dict) else []
    if not per_folio:
        return {
            "meta": {
                "version": "4.2",
                "description": "Empty flow field (no folios).",
            },
            "folio_ids": [],
            "flow_speed": [],
            "storm_index": [],
            "stability_index": [],
            "pressure_norm": [],
        }

    folio_ids = [f.get("folio_id") for f in per_folio]
    flow_speed = [_safe_float(f.get("flow_speed")) for f in per_folio]
    storm_index = [_safe_float(f.get("storm_index")) for f in per_folio]
    stability_index = [_safe_float(f.get("stability_index")) for f in per_folio]
    pressure_norm = [_safe_float(f.get("pressure_norm")) for f in per_folio]

    return {
        "meta": {
            "version": "4.2",
            "description": "Numeric semantic flow field over ordered folios.",
        },
        "folio_ids": folio_ids,
        "flow_speed": flow_speed,
        "storm_index": storm_index,
        "stability_index": stability_index,
        "pressure_norm": pressure_norm,
    }


def build_flow_segments(semantic_flow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify high-flow and low-flow segments:
      • high_flow_segments: continuous runs where flow_speed >= high_threshold
      • low_flow_segments : continuous runs where flow_speed <= low_threshold
    """
    per_folio = semantic_flow.get("per_folio", []) if isinstance(semantic_flow, dict) else []
    if not per_folio:
        return {
            "meta": {
                "version": "4.2",
                "description": "No segments (no folios).",
            },
            "high_flow_segments": [],
            "low_flow_segments": [],
        }

    speeds = [_safe_float(f.get("flow_speed")) for f in per_folio]
    if not speeds:
        return {
            "meta": {
                "version": "4.2",
                "description": "No segments (no speeds).",
            },
            "high_flow_segments": [],
            "low_flow_segments": [],
        }

    avg_speed = sum(speeds) / float(len(speeds))
    high_threshold = avg_speed * 1.2
    low_threshold = avg_speed * 0.6

    def collect_segments(predicate):
        segments = []
        current = []
        for idx, f in enumerate(per_folio):
            if predicate(speeds[idx]):
                current.append((idx, f))
            else:
                if current:
                    segments.append(_segment_to_summary(current))
                    current = []
        if current:
            segments.append(_segment_to_summary(current))
        return segments

    def _segment_to_summary(segment):
        indices = [idx for idx, _ in segment]
        folios = [f["folio_id"] for _, f in segment]
        speed_vals = [speeds[idx] for idx, _ in segment]
        return {
            "start_index": min(indices),
            "end_index": max(indices),
            "length": len(segment),
            "folio_ids": folios,
            "avg_flow_speed": sum(speed_vals) / float(len(speed_vals)),
        }

    high_segments = collect_segments(lambda s: s >= high_threshold)
    low_segments = collect_segments(lambda s: s <= low_threshold)

    return {
        "meta": {
            "version": "4.2",
            "description": "High-flow and low-flow segments in semantic flow field.",
        },
        "high_flow_segments": high_segments,
        "low_flow_segments": low_segments,
    }


def build_flow_topology(semantic_flow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build simple flow topology:
      • sources: high pressure_norm + rising flow_direction
      • sinks: low pressure_norm + falling flow_direction
      • shear_lines: folios classified as shear_flow or jet_stream
    """
    per_folio = semantic_flow.get("per_folio", []) if isinstance(semantic_flow, dict) else []
    if not per_folio:
        return {
            "meta": {
                "version": "4.2",
                "description": "Empty flow topology (no folios).",
            },
            "sources": [],
            "sinks": [],
            "shear_lines": [],
        }

    pressures = [_safe_float(f.get("pressure_norm")) for f in per_folio]
    p_min, p_max = min(pressures), max(pressures)
    # percentile-ish thresholds
    high_p = p_min + 0.75 * (p_max - p_min) if p_max > p_min else p_max
    low_p = p_min + 0.25 * (p_max - p_min) if p_max > p_min else p_min

    sources = []
    sinks = []
    shear_lines = []

    for f in per_folio:
        fid = f.get("folio_id")
        p = _safe_float(f.get("pressure_norm"))
        direction = f.get("flow_direction")
        category = f.get("flow_category")

        if p >= high_p and direction == "rising_pressure_flow":
            sources.append(
                {
                    "folio_id": fid,
                    "pressure_norm": p,
                    "flow_category": category,
                }
            )
        if p <= low_p and direction == "falling_pressure_flow":
            sinks.append(
                {
                    "folio_id": fid,
                    "pressure_norm": p,
                    "flow_category": category,
                }
            )
        if category in ("shear_flow", "jet_stream"):
            shear_lines.append(
                {
                    "folio_id": fid,
                    "flow_category": category,
                    "flow_speed": _safe_float(f.get("flow_speed")),
                }
            )

    return {
        "meta": {
            "version": "4.2",
            "description": "Simple flow topology (sources, sinks, shear lines).",
        },
        "sources": sources,
        "sinks": sinks,
        "shear_lines": shear_lines,
    }


# ────────────────────────────────────────────────────────────────────
# Pipeline
# ────────────────────────────────────────────────────────────────────

def run_v4_2_pipeline() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)

    semantic_weather = _load_json(SEMANTIC_WEATHER)
    weather_field = _load_json(WEATHER_FIELD)
    semantic_vortex = _load_json(SEMANTIC_VORTEX)
    semantic_isobars = _load_json(SEMANTIC_ISOBARS)

    semantic_flow = build_semantic_flow(
        semantic_weather=semantic_weather,
        weather_field=weather_field,
        semantic_vortex=semantic_vortex,
        semantic_isobars=semantic_isobars,
    )
    flow_field = build_flow_field(semantic_flow)
    flow_segments = build_flow_segments(semantic_flow)
    flow_topology = build_flow_topology(semantic_flow)

    _write_json(SEMANTIC_FLOW, semantic_flow)
    _write_json(FLOW_FIELD, flow_field)
    _write_json(FLOW_SEGMENTS, flow_segments)
    _write_json(FLOW_TOPOLOGY, flow_topology)

    # Ledger entry
    ts = datetime.now(timezone.utc).isoformat()
    stats = semantic_flow.get("stats", {})
    entry = {
        "timestamp": ts,
        "version": "4.2",
        "num_folios": stats.get("num_folios"),
        "speed_avg": stats.get("speed_avg"),
        "speed_min": stats.get("speed_min"),
        "speed_max": stats.get("speed_max"),
    }
    _append_ledger_entry(FLOW_LEDGER, entry)

    print(f"Semantic flow   → {SEMANTIC_FLOW}")
    print(f"Flow field      → {FLOW_FIELD}")
    print(f"Flow segments   → {FLOW_SEGMENTS}")
    print(f"Flow topology   → {FLOW_TOPOLOGY}")
    print(f"Ledger append   → {FLOW_LEDGER}")


if __name__ == "__main__":
    run_v4_2_pipeline()
