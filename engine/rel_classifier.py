\"\"\"REL classifier (public-safe stub).

Classifies common Voynich-style prefixes as relational
operators (REL). Mapping is static and finite.
\"\"\"

from typing import Optional

REL_PREFIXES = {
    "q": "REL_Q",
    "qo": "REL_QO",
    "ol": "REL_OL",
    "or": "REL_OR",
    "al": "REL_AL",
}

def classify_rel(token: str) -> Optional[str]:
    \"\"\"Return a REL label if the token begins with a known prefix.\"\"\"
    for pref, label in REL_PREFIXES.items():
        if token.startswith(pref):
            return label
    return None
