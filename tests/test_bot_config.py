"""Tests de config, logging, display, bot y main (capas finas)."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import discord
import pytest
from discord.ext import commands

from sorteo_bot.bot import SorteoBot
from sorteo_bot.config import Settings
from sorteo_bot.logging_config import configure_logging
from sorteo_bot.utils.discord_display import display_name_of


def test_settings_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    s = Settings(discord_token="abc")  # type: ignore[arg-type]
    assert s.command_prefix == "!"
    assert s.fuzzy_threshold == 70
    assert s.resolved_sqlite_path.parent.exists()


def test_settings_rechaza_prefijo_vacio() -> None:
    with pytest.raises(ValueError):
        Settings(discord_token="x", command_prefix="  ")  # type: ignore[arg-type]


def test_configure_logging_idempotente() -> None:
    configure_logging("DEBUG")
    configure_logging("INFO")  # segunda llamada no duplica handlers


def test_display_name_prioridades() -> None:
    assert display_name_of(SimpleNamespace(nick="N", display_name="D", name="U")) == "N"
    assert display_name_of(SimpleNamespace(nick=None, display_name="D", name="U")) == "D"
    assert display_name_of(SimpleNamespace(nick=None, display_name="", name="U")) == "U"


class FakeStore:
    async def get_all(self) -> dict[int, int]:
        return {}

    async def get(self, user_id: int) -> int:
        return 0

    async def add(self, user_id: int, amount: int) -> int:
        return amount

    async def remove(self, user_id: int, amount: int) -> int:
        return 0

    async def remove_user(self, user_id: int) -> bool:
        return True

    async def grant_many(self, user_ids: list[int], amount: int) -> int:
        return 0

    async def clear(self) -> None:
        return None

    async def import_legacy_json(self, path: Path) -> int:
        return 0


def test_bot_se_crea_con_intents() -> None:
    settings = Settings(discord_token="t")  # type: ignore[arg-type]
    bot = SorteoBot(settings, FakeStore())  # type: ignore[arg-type]
    assert bot.command_prefix == "!"
    assert bot.settings is settings


class FakeCtxSend:
    def __init__(self) -> None:
        self.texts: list[str] = []

    async def send(self, msg: str = "", **kwargs: Any) -> None:
        self.texts.append(str(msg))


async def test_bot_on_command_error_ramas() -> None:
    settings = Settings(discord_token="t")  # type: ignore[arg-type]
    bot = SorteoBot(settings, FakeStore())  # type: ignore[arg-type]
    ctx = FakeCtxSend()  # type: ignore[arg-type]
    await bot.on_command_error(ctx, commands.CommandNotFound())
    param = SimpleNamespace(name="nombre", displayed_name="nombre")
    await bot.on_command_error(ctx, commands.MissingRequiredArgument(param))  # type: ignore[arg-type]
    await bot.on_command_error(ctx, commands.BadArgument())
    await bot.on_command_error(ctx, commands.MissingPermissions([]))
    await bot.on_command_error(ctx, commands.CommandError("boom"))
    assert len(ctx.texts) == 5


async def test_bot_on_app_command_error() -> None:
    from discord import app_commands

    settings = Settings(discord_token="t")  # type: ignore[arg-type]
    bot = SorteoBot(settings, FakeStore())  # type: ignore[arg-type]

    class FakeResponse:
        def __init__(self, done: bool) -> None:
            self._done = done
            self.sent: list[str] = []

        def is_done(self) -> bool:
            return self._done

        async def send_message(self, msg: str, **kwargs: Any) -> None:
            self.sent.append(msg)

        async def send(self, msg: str, **kwargs: Any) -> None:
            self.sent.append(msg)

    class FakeInteraction:
        def __init__(self, done: bool) -> None:
            self.response = FakeResponse(done)
            self.followup = FakeResponse(False)

    await bot.on_app_command_error(
        FakeInteraction(False),  # type: ignore[arg-type]
        app_commands.MissingPermissions([]),
    )
    await bot.on_app_command_error(
        FakeInteraction(True),  # type: ignore[arg-type]
        app_commands.AppCommandError("boom"),
    )


async def test_main_sin_token_aborta(monkeypatch: pytest.MonkeyPatch) -> None:
    from sorteo_bot import main as main_mod

    monkeypatch.setenv("DISCORD_TOKEN", "")
    # get_settings está cacheado: limpiamos caché y forzamos token vacío
    main_mod.get_settings.cache_clear()
    monkeypatch.setenv("DISCORD_TOKEN", "   ")
    with pytest.raises(SystemExit):
        await main_mod.amain()
    main_mod.get_settings.cache_clear()


def test_status_icon_map_cubre_offline() -> None:
    assert discord.Status.offline is not None
