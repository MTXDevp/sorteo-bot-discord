"""Tests del sorteo ponderado."""

import random
from collections import Counter

import pytest

from sorteo_bot.domain.draw import choose_weighted_winner, probabilities
from sorteo_bot.domain.errors import NoParticipantsError


def test_probabilities_suman_uno() -> None:
    probs = probabilities({1: 1, 2: 3})
    assert probs == pytest.approx({1: 0.25, 2: 0.75})
    assert sum(probs.values()) == pytest.approx(1.0)


def test_probabilities_vacio_lanza() -> None:
    with pytest.raises(NoParticipantsError):
        probabilities({})


def test_winner_es_ponderado(rng: random.Random) -> None:
    # 1 entrada frente a 99: el pesado debe ganar ~99 % de las veces.
    counts: Counter[int] = Counter(
        choose_weighted_winner({1: 1, 2: 99}, rng=rng) for _ in range(1000)
    )
    assert counts[2] > 900
    assert counts[1] > 0  # el ligero aún puede ganar (aleatoriedad real)


def test_winner_determinista_con_semilla() -> None:
    a = choose_weighted_winner({1: 5, 2: 3, 3: 2}, rng=random.Random(7))
    b = choose_weighted_winner({1: 5, 2: 3, 3: 2}, rng=random.Random(7))
    assert a == b


def test_winner_vacio_lanza() -> None:
    with pytest.raises(NoParticipantsError):
        choose_weighted_winner({})


def test_pesos_invalidos_lanzan() -> None:
    with pytest.raises(ValueError):
        choose_weighted_winner({1: 0})
    with pytest.raises(ValueError):
        probabilities({1: -2})
