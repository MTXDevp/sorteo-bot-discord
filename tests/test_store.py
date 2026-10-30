"""Tests del repositorio SQLite (usa BD temporal por test)."""

import json
from pathlib import Path

import pytest

from sorteo_bot.domain.errors import InsufficientEntriesError, InvalidEntriesError
from sorteo_bot.infrastructure.store import SqliteParticipationStore


@pytest.fixture()
async def store(tmp_path: Path) -> SqliteParticipationStore:
    s = SqliteParticipationStore(tmp_path / "test.db")
    await s.initialize()
    return s


async def test_add_y_get(store: SqliteParticipationStore) -> None:
    assert await store.get(1) == 0
    assert await store.add(1, 3) == 3
    assert await store.add(1, 2) == 5
    assert await store.get(1) == 5


async def test_add_invalido(store: SqliteParticipationStore) -> None:
    with pytest.raises(InvalidEntriesError):
        await store.add(1, 0)


async def test_remove_y_borrado_automatico(store: SqliteParticipationStore) -> None:
    await store.add(7, 5)
    assert await store.remove(7, 2) == 3
    assert await store.remove(7, 3) == 0
    assert await store.get(7) == 0


async def test_remove_sin_saldo(store: SqliteParticipationStore) -> None:
    with pytest.raises(InsufficientEntriesError):
        await store.remove(99, 1)


async def test_grant_many_y_clear(store: SqliteParticipationStore) -> None:
    assert await store.grant_many([1, 2, 3], 2) == 3
    assert await store.get_all() == {1: 2, 2: 2, 3: 2}
    await store.clear()
    assert await store.get_all() == {}


async def test_import_legacy_json(tmp_path: Path) -> None:
    legacy = tmp_path / "participaciones.json"
    legacy.write_text(json.dumps({"11": 4, "22": 1}), encoding="utf-8")
    store = SqliteParticipationStore(tmp_path / "migrada.db")
    assert await store.import_legacy_json(legacy) == 2
    assert await store.get_all() == {11: 4, 22: 1}
