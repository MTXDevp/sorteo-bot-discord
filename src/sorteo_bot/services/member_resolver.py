from collections.abc import Iterable
from typing import Protocol

from rapidfuzz import fuzz

from sorteo_bot.utils.text import normalize_text


class NamedMember(Protocol):
    @property
    def id(self) -> int: ...
    @property
    def display_name(self) -> str: ...


def resolve_member_id(
    members: Iterable[NamedMember],
    query: str,
    *,
    threshold: int = 70,
) -> int | None:
    # La gente escribe los nombres como le da la gana: "jose", "José García", "josé".
    # Primero pruebo exacto, luego normalizado y al final difuso. Con 70 va bien.
    cleaned = query.strip()
    if not cleaned:
        return None

    candidates = list(members)

    for member in candidates:
        if member.display_name == cleaned:
            return member.id

    wanted = normalize_text(cleaned)
    for member in candidates:
        if normalize_text(member.display_name) == wanted:
            return member.id

    best_id: int | None = None
    best_score: float = float(threshold)
    for member in candidates:
        score = fuzz.ratio(wanted, normalize_text(member.display_name))
        if score >= best_score:
            best_score = score
            best_id = member.id
    return best_id
