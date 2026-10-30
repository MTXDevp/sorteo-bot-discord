"""Tests de normalización y resolución de miembros."""

from dataclasses import dataclass

from sorteo_bot.services.member_resolver import resolve_member_id
from sorteo_bot.utils.text import normalize_text


@dataclass
class FakeMember:
    id: int
    display_name: str


def test_normalize_quita_tildes_y_espacios() -> None:
    assert normalize_text("  José   García  ") == "jose garcia"
    assert normalize_text("NIÑO") == "nino"


def test_resolve_exacta() -> None:
    members = [FakeMember(1, "Ana"), FakeMember(2, "Beto")]
    assert resolve_member_id(members, "Ana") == 1


def test_resolve_tolerante_a_tildes() -> None:
    members = [FakeMember(10, "José García")]
    assert resolve_member_id(members, "jose garcia") == 10
    assert resolve_member_id(members, "  JOSÉ GARCÍA  ") == 10


def test_resolve_difusa_por_umbral() -> None:
    members = [FakeMember(5, "Katherine"), FakeMember(6, "Pedro")]
    assert resolve_member_id(members, "Katherin", threshold=70) == 5


def test_resolve_none_si_no_hay_match() -> None:
    members = [FakeMember(1, "Ana")]
    assert resolve_member_id(members, "Zzzzzz", threshold=95) is None
    assert resolve_member_id(members, "   ") is None
