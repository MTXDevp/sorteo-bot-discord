import random
from collections.abc import Mapping

from sorteo_bot.domain.errors import NoParticipantsError


def probabilities(entries_by_user: Mapping[int, int]) -> dict[int, float]:
    # probabilidad de cada uno = sus participaciones / total. Sin más.
    if not entries_by_user:
        raise NoParticipantsError("No hay participaciones para calcular probabilidades.")
    if any(v <= 0 for v in entries_by_user.values()):
        raise ValueError("Todas las participaciones deben ser > 0.")
    total = sum(entries_by_user.values())
    if total <= 0:
        raise NoParticipantsError("No hay participaciones para calcular probabilidades.")
    return {user_id: entries / total for user_id, entries in entries_by_user.items()}


def choose_weighted_winner(
    entries_by_user: Mapping[int, int],
    rng: random.Random | None = None,
) -> int:
    # El que más participaciones tiene más papeletas. random.choices lo hace bien.
    if not entries_by_user:
        raise NoParticipantsError("No hay participantes en el sorteo.")
    if any(v <= 0 for v in entries_by_user.values()):
        raise ValueError("Todas las participaciones deben ser > 0.")

    if rng is None:
        rng = random.Random()
    population = list(entries_by_user.keys())
    weights = [entries_by_user[user_id] for user_id in population]
    return rng.choices(population, weights=weights, k=1)[0]
