import re
import unicodedata

_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    # "  José   García " -> "jose garcia". Para buscar sin pelearte con tildes.
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = decomposed.encode("ASCII", "ignore").decode("ASCII")
    return _WHITESPACE.sub(" ", ascii_only).strip().lower()
