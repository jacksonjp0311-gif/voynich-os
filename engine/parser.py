\"\"\"Voynich OS parser (public-safe).

Consumes tokens and produces a simple structural
representation. Deterministic and non-adaptive.
\"\"\"

from typing import List, Dict

def parse(tokens: List[str]) -> List[Dict]:
    \"\"\"Return a list of dicts with basic token metadata.\"\"\"
    result: List[Dict] = []
    for index, t in enumerate(tokens):
        entry = {
            "index": index,
            "text": t,
            "length": len(t),
        }
        result.append(entry)
    return result
