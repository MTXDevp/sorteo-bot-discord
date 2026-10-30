"""Tests del modelo de dominio."""

import pytest

from sorteo_bot.domain.models import Participant


def test_participant_valido() -> None:
    p = Participant(user_id=123, entries=2)
    assert (p.user_id, p.entries) == (123, 2)


def test_participant_invalido() -> None:
    with pytest.raises(ValueError):
        Participant(user_id=0, entries=1)
    with pytest.raises(ValueError):
        Participant(user_id=1, entries=0)
