\"\"\"Voynich OS tokenizer (public-safe stub).

Splits a line of EVA text into simple glyph tokens.
Currently uses whitespace splitting; can be extended with
more precise glyph segmentation rules.
\"\"\"

from typing import List

def tokenize(text: str) -> List[str]:
    \"\"\"Return a list of tokens from a line of EVA text.\"\"\"
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return text.strip().split()
