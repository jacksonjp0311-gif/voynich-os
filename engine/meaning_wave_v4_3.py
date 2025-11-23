"""Voynich OS — Meaning Wave Engine v4.3
Deterministic semantic wave-field synthesis.

Inputs
------
  • v4_0: semantic_vortex_v4_0.json
  • v4_1: isobar_map_v4_1.json
  • v4_2: semantic_flow_v4_2.json
  • v3_9: semantic_weather_v3_9.json

Outputs → data/meaning_v4_3/
----------------------------------
  • meaning_wave_v4_3.json
  • wave_lattice_v4_3.json
  • wave_spectrum_v4_3.json
  • wave_ledger_v4_3.jsonl

All logic is deterministic, analytic, non-adaptive, and safe.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[1]

VORTEX  = REPO/"data/meaning_v4_0/semantic_vortex_v4_0.json"
ISOBAR  = REPO/"data/meaning_v4_1/isobar_map_v4_1.json"
FLOW    = REPO/"data/meaning_v4_2/semantic_flow_v4_2.json"
WEATHER = REPO/"data/meaning_v3_9/semantic_weather_v3_9.json"

OUTDIR  = REPO/"data/meaning_v4_3"
WAVE    = OUTDIR/"meaning_wave_v4_3.json"
LATTICE = OUTDIR/"wave_lattice_v4_3.json"
SPECTRUM= OUTDIR/"wave_spectrum_v4_3.json"
LEDGER  = OUTDIR/"wave_ledger_v4_3.jsonl"

def _load(p):
    p = Path(p)
    if not p.exists():
        raise FileNotFoundError(f"Missing required input: {p}")
    return json.load(p.open("r",encoding="utf-8"))

def _write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8") as f: json.dump(data,f,indent=2,sort_keys=True)

def _append(p,entry):
    line = json.dumps(entry,sort_keys=True)
    with p.open("a",encoding="utf-8") as f: f.write(line+"\n")

# ──────────────────────────────
# Wavefield synthesis
# ──────────────────────────────

def build_wavefield(vortex,isobar,flow,weather):
    folios = sorted({f["folio_id"] for f in flow.get("per_folio",[])})
    out = []

    flow_map = {f["folio_id"]:f for f in flow.get("per_folio",[])}
    weather_map = {f["folio_id"]:f for f in weather.get("per_folio",[])}

    iso = isobar.get("per_folio",[])
    iso_map = {f["folio_id"]:f for f in iso}

    for fid in folios:
        f = flow_map.get(fid,{})
        w = weather_map.get(fid,{})
        i = iso_map.get(fid,{})

        press = i.get("isobar_level",0.0)
        vortex_strength = vortex.get("vortex_strength",{}).get(fid,0.0)

        cont = f.get("continuity_norm",0.0)
        drift = w.get("drift_index",0.0)
        stab = w.get("stability_index",0.0)
        storm= w.get("storm_index",0.0)

        amp = max(0.0, cont + press - drift)
        freq = max(0.0, vortex_strength + storm*0.5)
        phase = max(0.0, stab - drift/2)

        out.append({
            "folio_id":fid,
            "amplitude":amp,
            "frequency":freq,
            "phase":phase,
            "theme": f.get("dominant_theme"),
        })
    return out

# lattice = adjacency-like smoothing
def build_lattice(wave):
    ids = [w["folio_id"] for w in wave]
    lattice=[]
    for i,fid in enumerate(ids):
        left  = ids[i-1] if i>0 else None
        right = ids[i+1] if i<len(ids)-1 else None
        lattice.append({
            "folio_id":fid,
            "neighbors":[n for n in (left,right) if n]
        })
    return lattice

def build_spectrum(wave):
    return {
        "meta":{"description":"compact semantic wave spectrum"},
        "amplitude":[w["amplitude"] for w in wave],
        "frequency":[w["frequency"] for w in wave],
        "phase":[w["phase"] for w in wave],
        "folio_ids":[w["folio_id"] for w in wave]
    }

# ──────────────────────────────
# Pipeline
# ──────────────────────────────

def run():
    OUTDIR.mkdir(parents=True,exist_ok=True)

    vortex  = _load(VORTEX)
    isobar  = _load(ISOBAR)
    flow    = _load(FLOW)
    weather = _load(WEATHER)

    wave = build_wavefield(vortex,isobar,flow,weather)
    lattice = build_lattice(wave)
    spec = build_spectrum(wave)

    _write(WAVE,wave)
    _write(LATTICE,lattice)
    _write(SPECTRUM,spec)

    entry = {
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "version":"4.3",
        "wave_count":len(wave),
    }
    _append(LEDGER,entry)

    print("Wavefield  →",WAVE)
    print("Lattice    →",LATTICE)
    print("Spectrum   →",SPECTRUM)
    print("Ledger     →",LEDGER)

if __name__=="__main__":
    run()
