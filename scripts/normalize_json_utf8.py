from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    ROOT / "data" / "folio_outputs",
    ROOT / "data" / "meaning",
    ROOT / "data" / "manuscript_v12_0",
    ROOT / "data" / "hybrid_v1_0",
    ROOT / "data" / "fields_v11",
    ROOT / "state",
]

def normalize_json_file(path: Path) -> bool:
    raw = path.read_bytes()
    had_bom = raw.startswith(b"\xef\xbb\xbf")

    text = raw.decode("utf-8-sig")
    obj = json.loads(text)

    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return had_bom

def main() -> int:
    checked = 0
    normalized = []

    for root in TARGETS:
        if not root.exists():
            continue

        for path in root.rglob("*.json"):
            checked += 1
            had_bom = normalize_json_file(path)
            if had_bom:
                normalized.append(str(path.relative_to(ROOT)))

    report = {
        "artifact": "Voynich OS JSON BOM normalization",
        "version": "v12.1.1",
        "checked_json_files": checked,
        "bom_files_normalized": normalized,
        "normalized_count": len(normalized),
    }

    out = ROOT / "state" / "audits" / "voynich_json_bom_normalization_v12_1_1.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("")
    print(f"Wrote: {out.relative_to(ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())