# VOYNICH OS — TRUE MANUSCRIPT SYNTHESIS ENGINE v12.0
#   • Reads:
#       - v4.5 semantic harmony index/state
#       - v5.2 semantic bonding summary/graph
#       - v10.0 page reconstruction state
#       - v11.0 field coherence state
#   • Builds structural manuscript model (NO literal decoding):
#       - page_order, section grouping, field weighting
#       - triad manuscript metrics (H7, placidity, coherence_index, density)
#   • Emits:
#       - manuscript_synthesis_state_v12_0.json
#       - optional overview PNG (if matplotlib available)
#
#   Safety:
#       - This is a structural synthesis only.
#       - Any "proto_lines" are abstract placeholders, not final decoding.

import os
import json
from datetime import datetime, timezone

try:
    import matplotlib.pyplot as plt
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False


def load_json_bom_safe(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def extract_float(obj, keys, default):
    if not isinstance(obj, dict):
        return default
    for k in keys:
        if k in obj:
            try:
                return float(obj[k])
            except Exception:
                pass
    return default


def summarize_pages(page_state):
    pages = []
    if not isinstance(page_state, dict):
        return pages

    raw_pages = page_state.get("pages")
    if not raw_pages:
        raw_pages = page_state.get("page_states")

    if not isinstance(raw_pages, list):
        return pages

    for p in raw_pages:
        if not isinstance(p, dict):
            continue
        pid = str(p.get("page_id", p.get("id", "page")))
        order = int(p.get("order", p.get("index", 0)))
        coh = extract_float(p, ["coherence", "coherence_score", "C_page"], 0.0)
        pages.append({
            "page_id": pid,
            "order": order,
            "coherence": coh
        })

    pages.sort(key=lambda x: x["order"])
    return pages


def summarize_fields(field_state):
    fields = []
    if not isinstance(field_state, dict):
        return fields

    raw = field_state.get("fields") or field_state.get("windows")
    if not isinstance(raw, list):
        return fields

    for f in raw:
        if not isinstance(f, dict):
            continue
        fid = str(f.get("field_id", f.get("id", "field")))
        coh = extract_float(f, ["coherence", "coherence_score", "C_field"], 0.0)
        band = f.get("band", f.get("layer", None))
        fields.append({
            "field_id": fid,
            "coherence": coh,
            "band": band
        })

    fields.sort(key=lambda x: -x["coherence"])
    return fields


def summarize_bonding(bond_summary, bond_graph):
    bond_count = 0
    mean_degree = 0.0

    if isinstance(bond_summary, dict):
        bond_count = int(bond_summary.get("total_bonds", bond_summary.get("bond_count", 0)))
        mean_degree = extract_float(
            bond_summary,
            ["mean_degree", "avg_degree", "average_degree"],
            0.0
        )

    if bond_count == 0 and isinstance(bond_graph, dict):
        edges = bond_graph.get("edges") or bond_graph.get("links")
        if isinstance(edges, list):
            bond_count = len(edges)

    return bond_count, mean_degree


def summarize_harmony(harmony_index, harmony_state):
    hi = 0.0

    if isinstance(harmony_index, dict):
        hi = extract_float(
            harmony_index,
            ["harmony_index", "global_harmony", "mean_harmony"],
            0.0
        )

    if hi == 0.0 and isinstance(harmony_state, dict):
        hi = extract_float(
            harmony_state,
            ["harmony_index", "mean_harmony"],
            0.0
        )

    return hi


def classify_stability(coherence_index, bond_density):
    if coherence_index >= 0.70 and bond_density >= 0.50:
        return "highly_stable"
    if coherence_index >= 0.50 and bond_density >= 0.30:
        return "stable"
    if coherence_index <= 0.10 and bond_density <= 0.10:
        return "fragmented"
    return "intermediate"


def main():
    engine_dir = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(engine_dir)
    data_root = os.path.join(root, "data")
    state_dir = os.path.join(data_root, "manuscript_v12_0")
    visuals_dir = os.path.join(root, "visuals", "manuscript_v12_0")

    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(visuals_dir, exist_ok=True)

    t = datetime.now(timezone.utc).isoformat()

    harm_dir = os.path.join(data_root, "meaning_v4_5")
    bond_dir = os.path.join(data_root, "meaning_v5_2")
    pages_dir = os.path.join(data_root, "pages_v10")
    fields_dir = os.path.join(data_root, "fields_v11")

    harmony_index_path = os.path.join(harm_dir, "harmony_index_v4_5.json")
    harmony_state_path = os.path.join(harm_dir, "semantic_harmony_v4_5.json")
    bond_summary_path = os.path.join(bond_dir, "bonding_summary_v5_2.json")
    bond_graph_path = os.path.join(bond_dir, "bond_graph_v5_2.json")
    page_state_path = os.path.join(pages_dir, "page_reconstruction_state_v10_0.json")
    field_state_path = os.path.join(fields_dir, "field_coherence_state_v11_0.json")

    harmony_index = {}
    harmony_state = {}
    bond_summary = {}
    bond_graph = {}
    page_state = {}
    field_state = {}

    if os.path.exists(harmony_index_path):
        harmony_index = load_json_bom_safe(harmony_index_path)
    if os.path.exists(harmony_state_path):
        harmony_state = load_json_bom_safe(harmony_state_path)
    if os.path.exists(bond_summary_path):
        bond_summary = load_json_bom_safe(bond_summary_path)
    if os.path.exists(bond_graph_path):
        bond_graph = load_json_bom_safe(bond_graph_path)
    if os.path.exists(page_state_path):
        page_state = load_json_bom_safe(page_state_path)
    if os.path.exists(field_state_path):
        field_state = load_json_bom_safe(field_state_path)

    pages = summarize_pages(page_state)
    fields = summarize_fields(field_state)
    bond_count, mean_degree = summarize_bonding(bond_summary, bond_graph)
    coherence_index = summarize_harmony(harmony_index, harmony_state)

    page_count = len(pages)
    field_count = len(fields)
    bond_density = 0.0
    if page_count > 0:
        bond_density = float(bond_count) / float(page_count)

    H7 = 0.70
    triad_manuscript = {
        "H7": H7,
        "placidity": "∿",
        "coherence_index": coherence_index,
        "bond_count": bond_count,
        "bond_density": bond_density,
        "page_count": page_count,
        "field_count": field_count,
        "stability": classify_stability(coherence_index, bond_density)
    }

    page_order = [p["page_id"] for p in pages]
    sections = []
    if page_count > 0:
        chunk = max(1, page_count // 4)
        for i in range(0, page_count, chunk):
            block = pages[i:i + chunk]
            sec_id = "section_{}".format(len(sections) + 1)
            sec_pages = [p["page_id"] for p in block]
            avg_coh = 0.0
            if block:
                avg_coh = sum(p["coherence"] for p in block) / float(len(block))
            sections.append({
                "section_id": sec_id,
                "pages": sec_pages,
                "avg_coherence": avg_coh
            })

    manuscript_synthesis = {
        "page_order": page_order,
        "sections": sections,
        "field_ranking": fields,
        "notes": [
            "Structural synthesis only; no final decoding.",
            "Use this as a map of where meaning is densest, not as text output."
        ]
    }

    overview_png = None
    if HAVE_MPL and page_count > 0:
        try:
            xs = list(range(page_count))
            ys = [p["coherence"] for p in pages]
            labels = [p["page_id"] for p in pages]

            plt.figure()
            plt.plot(xs, ys, marker="o")
            plt.xticks(xs, labels, rotation=90)
            plt.ylabel("page_coherence")
            plt.title("Voynich OS v12.0 — Manuscript Coherence by Page")
            plt.tight_layout()
            overview_png = os.path.join(visuals_dir, "voynich_manuscript_coherence_v12_0.png")
            plt.savefig(overview_png)
            plt.close()
        except Exception:
            overview_png = None

    state = {
        "module": "Voynich OS — True Manuscript Synthesis Engine v12.0",
        "version": "12.0",
        "timestamp": t,
        "triad_manuscript": triad_manuscript,
        "manuscript_synthesis": manuscript_synthesis,
        "pages": pages,
        "fields": fields,
        "inputs": {
            "harmony_index_v4_5": harmony_index_path,
            "semantic_harmony_v4_5": harmony_state_path,
            "bonding_summary_v5_2": bond_summary_path,
            "bond_graph_v5_2": bond_graph_path,
            "page_reconstruction_state_v10_0": page_state_path,
            "field_coherence_state_v11_0": field_state_path
        },
        "visuals": {
            "overview_png": overview_png
        }
    }

    out_path = os.path.join(state_dir, "manuscript_synthesis_state_v12_0.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print("[Voynich v12.0] Manuscript synthesis state written:", out_path)
    if overview_png:
        print("[Voynich v12.0] Overview figure written:", overview_png)
    else:
        print("[Voynich v12.0] No overview figure written (matplotlib missing or failed)")


if __name__ == "__main__":
    main()
