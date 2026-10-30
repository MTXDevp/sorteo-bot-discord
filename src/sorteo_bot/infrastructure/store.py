import asyncio
import json
import logging
from pathlib import Path
from typing import Protocol

import aiosqlite

from sorteo_bot.domain.errors import InsufficientEntriesError, InvalidEntriesError

log = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS participations (
    user_id INTEGER PRIMARY KEY,
    entries INTEGER NOT NULL CHECK (entries > 0)
);
"""


class ParticipationRepository(Protocol):
    async def get_all(self) -> dict[int, int]: ...
    async def get(self, user_id: int) -> int: ...
    async def add(self, user_id: int, amount: int) -> int: ...
    async def remove(self, user_id: int, amount: int) -> int: ...
    async def remove_user(self, user_id: int) -> bool: ...
    async def grant_many(self, user_ids: list[int], amount: int) -> int: ...
    async def clear(self) -> None: ...
    async def import_legacy_json(self, path: Path) -> int: ...


class SqliteParticipationStore:
    # SQLite porque con un JSON a la segunda ejecución concurrente se corrompía.
    # Una fila por usuario, nada más. Suficiente para este bot.
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        async with self._lock:
            await self._initialize_locked()

    async def _initialize_locked(self) -> None:
        if self._initialized:
            return
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self._db_path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()
        self._initialized = True

    async def _ensure_ready(self) -> None:
        if not self._initialized:
            await self.initialize()

    @staticmethod
    def _validate_amount(amount: int) -> None:
        if amount <= 0:
            raise InvalidEntriesError(amount)

    async def get_all(self) -> dict[int, int]:
        await self._ensure_ready()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("SELECT user_id, entries FROM participations")
            rows = await cursor.fetchall()
        return {int(user_id): int(entries) for user_id, entries in rows}

    async def get(self, user_id: int) -> int:
        await self._ensure_ready()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT entries FROM participations WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def add(self, user_id: int, amount: int) -> int:
        self._validate_amount(amount)
        await self._ensure_ready()
        async with self._lock, aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO participations (user_id, entries)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET entries = entries + excluded.entries
                """,
                (user_id, amount),
            )
            await db.commit()
            cursor = await db.execute(
                "SELECT entries FROM participations WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def remove(self, user_id: int, amount: int) -> int:
        self._validate_amount(amount)
        await self._ensure_ready()
        async with self._lock, aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT entries FROM participations WHERE user_id = ?", (user_id,)
            )
            row = await cursor.fetchone()
            current = int(row[0]) if row else 0
            if current < amount:
                raise InsufficientEntriesError(
                    f"user={user_id} tiene {current}, se pidieron {amount}."
                )
            remaining = current - amount
            if remaining == 0:
                await db.execute("DELETE FROM participations WHERE user_id = ?", (user_id,))
            else:
                await db.execute(
                    "UPDATE participations SET entries = ? WHERE user_id = ?",
                    (remaining, user_id),
                )
            await db.commit()
        return remaining

    async def remove_user(self, user_id: int) -> bool:
        await self._ensure_ready()
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("DELETE FROM participations WHERE user_id = ?", (user_id,))
            await db.commit()
            return (cursor.rowcount or 0) > 0

    async def grant_many(self, user_ids: list[int], amount: int) -> int:
        self._validate_amount(amount)
        if not user_ids:
            return 0
        await self._ensure_ready()
        async with self._lock, aiosqlite.connect(self._db_path) as db:
            await db.executemany(
                """
                INSERT INTO participations (user_id, entries)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET entries = entries + excluded.entries
                """,
                [(uid, amount) for uid in user_ids],
            )
            await db.commit()
        return len(user_ids)

    async def clear(self) -> None:
        await self._ensure_ready()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM participations")
            await db.commit()

    async def import_legacy_json(self, path: Path) -> int:
        # El bot original guardaba en participaciones.json. Lo migro una vez y listo.
        exists = await asyncio.to_thread(path.exists)
        if not exists:
            return 0
        text = await asyncio.to_thread(path.read_text, encoding="utf-8")
        raw = json.loads(text or "{}")
        if not isinstance(raw, dict):
            return 0
        pairs = [(int(uid), int(n)) for uid, n in raw.items() if int(n) > 0]
        if not pairs:
            return 0
        await self._ensure_ready()
        async with self._lock, aiosqlite.connect(self._db_path) as db:
            await db.executemany(
                """
                INSERT INTO participations (user_id, entries)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET entries = entries + excluded.entries
                """,
                pairs,
            )
            await db.commit()
        log.info("Migradas %d entradas desde %s", len(pairs), path)
        return len(pairs)
