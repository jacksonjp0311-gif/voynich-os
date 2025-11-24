import json, pathlib, datetime
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
IMPORT_DIR = ROOT / "import_v4_5"

# Upstream
FLOW_PATH     = DATA/"meaning_v4_2"/"semantic_flow_v4_2.json"
WAVE_PATH     = DATA/"meaning_v4_3"/"meaning_wave_v4_3.json"
RES_PATH      = DATA/"meaning_v4_4"/"semantic_resonance_v4_4.json"
HARM_PATH     = DATA/"meaning_v4_5"/"semantic_harmony_v4_5.json"
FIELD_PATH    = DATA/"meaning_v4_7"/"meaning_field_v4_7.json"
VEC_PATH      = DATA/"meaning_v4_8"/"meaning_vector_v4_8.json"
ATTR_MAP      = DATA/"meaning_v4_9"/"semantic_attractor_map_v4_9.json"
ATTR_SUM      = DATA/"meaning_v4_9"/"attractor_summary_v4_9.json"
IMPORT_JSON   = IMPORT_DIR/"uploaded_payload_v4_5.json"

OUT = DATA/"meaning_v5_0"
OUT.mkdir(parents=True, exist_ok=True)

SURFACE = OUT/"translation_surface_v5_0.json"
SENT    = OUT/"translation_sentences_v5_0.json"
WIN     = OUT/"translation_windows_v5_0.json"
SUM     = OUT/"translation_summary_v5_0.json"
LEDGER  = OUT/"translation_ledger_v5_0.jsonl"

def safe_load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def run():
    time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    flow   = safe_load(FLOW_PATH, {})
    wave   = safe_load(WAVE_PATH, {})
    res    = safe_load(RES_PATH, {})
    harm   = safe_load(HARM_PATH, {})
    field  = safe_load(FIELD_PATH, {})
    vec    = safe_load(VEC_PATH, {})
    amap   = safe_load(ATTR_MAP, {})
    asum   = safe_load(ATTR_SUM, {})
    imp    = safe_load(IMPORT_JSON, {})

    coh = 0.0
    weights = {"flow":0,"wave":0,"resonance":0,"harmony":0,"field":0,"vectors":0}

    if isinstance(asum, dict):
        try: coh = float(asum.get("coherence",0))
        except: coh = 0.0
        sw = asum.get("stage_weights",{})
        if isinstance(sw, dict):
            for k,v in sw.items():
                try: weights[k] = float(v)
                except: weights[k] = 0.0

    # Proto sentences
    sentences = []
    attractors = amap.get("attractors",[]) if isinstance(amap,dict) else []
    if not attractors:
        sentences.append({
            "id":"S0",
            "surface_line":"Translation surface initialized (no attractors).",
            "coherence":0.0
        })
    else:
        ordered = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
        top = [n for n,_ in ordered[:3]]
        for i,a in enumerate(attractors):
            cid = a.get("id",f"A{i}")
            label = a.get("label","attractor")
            c = a.get("coherence",0.0)
            line = f"{cid} ({label}) aligns meaning around {top} with coherence ≈ {round(c*100,2)}%."
            sentences.append({
                "id":f"S{i}",
                "attractor_id":cid,
                "coherence":c,
                "surface_line":line,
                "top_stages":top
            })

    # Windows
    windows = []
    ordered = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    for i,(name,w) in enumerate(ordered):
        windows.append({
            "id":f"W{i}",
            "stage":name,
            "weight":w,
            "hint":f"Meaning pressure ≈ {round(w*100,2)}% on stage {name}."
        })

    # Surface
    surface = {
        "meta":{
            "version":"5.0",
            "timestamp":time,
            "description":"Voynich Translation Surface v5.0"
        },
        "coherence":coh,
        "stage_weights":weights
    }

    summary = {
        "version":"5.0",
        "timestamp":time,
        "coherence":coh,
        "num_sentences":len(sentences),
        "num_windows":len(windows)
    }

    def dump(p,obj):
        p.write_text(json.dumps(obj,indent=2),encoding="utf-8")

    dump(SURFACE,surface)
    dump(SENT,{"sentences":sentences})
    dump(WIN,{"windows":windows})
    dump(SUM,summary)
    LEDGER.open("a",encoding="utf-8").write(json.dumps(summary)+"\n")

    print("v5.0 Translation Surface →", SURFACE)
    print("v5.0 Sentences          →", SENT)
    print("v5.0 Windows            →", WIN)
    print("v5.0 Summary            →", SUM)
    print("v5.0 Ledger append      →", LEDGER)

if __name__ == "__main__":
    run()
