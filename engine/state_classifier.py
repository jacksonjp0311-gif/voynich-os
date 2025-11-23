\"\"\"STATE classifier (public-safe).

Maps common Voynich-style suffixes to simple state
labels. Mapping is static and non-adaptive.
\"\"\"

from typing import Optional

STATE_SUFFIXES = {
    "y": "STATE_Y",
    "dy": "STATE_DY",
    "ain": "STATE_AIN",
    "aiin": "STATE_AIIN",
    "chedy": "STATE_CHEDY",
}

def classify_state(token: str) -> Optional[str]:
    \"\"\"Return a STATE label if the token ends with a known suffix.\"\"\"
    for suff, label in STATE_SUFFIXES.items():
        if token.endswith(suff):
            return label
    return None
