\"\"\"Voynich OS tokenizer (public-safe).

Splits a line of EVA text into glyph tokens.
Currently uses whitespace splitting; can later
be extended with more precise glyph segmentation.
\"\"\"

from typing import List

def tokenize(text: str) -> List[str]:
    \"\"\"Return a list of tokens from a line of EVA text.\"\"\"
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    text = text.strip()
    if not text:
        return []
    return text.split()
