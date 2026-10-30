"""Tests de los Cogs con dobles de Discord (sin red)."""

from types import SimpleNamespace
from typing import Any

import discord

from sorteo_bot.cogs.consulta import ConsultaCog
from sorteo_bot.cogs.participaciones import ParticipacionesAdminCog
from sorteo_bot.cogs.sorteo import SorteoCog
from sorteo_bot.config import Settings


class FakeMember:
    def __init__(
        self,
        id: int,
        display_name: str,
        bot: bool = False,
        status: discord.Status = discord.Status.online,
        nick: str | None = None,
    ) -> None:
        self.id = id
        self.display_name = display_name
        self.nick = nick
        self.name = display_name
        self.bot = bot
        self.status = status


class FakeVoiceChannel:
    def __init__(self, name: str, members: list[FakeMember] | None = None) -> None:
        self.name = name
        self.members: list[FakeMember] = members or []
        self.connected = False

    async def connect(self) -> None:
        self.connected = True


class FakeGuild:
    def __init__(
        self,
        members: list[FakeMember] | None = None,
        voice_channels: list[FakeVoiceChannel] | None = None,
    ) -> None:
        self.members: list[FakeMember] = members or []
        self.voice_channels: list[FakeVoiceChannel] = voice_channels or []
        self.voice_client: Any = None

    def get_member(self, user_id: int) -> FakeMember | None:
        return next((m for m in self.members if m.id == user_id), None)


class FakeMessage:
    def __init__(self) -> None:
        self.deleted = False

    async def delete(self) -> None:
        self.deleted = True


class FakeCtx:
    def __init__(self, guild: FakeGuild | None, author_id: int = 999) -> None:
        self.guild = guild  # type: ignore[assignment]
        self.author = SimpleNamespace(id=author_id)
        self.sent: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    async def send(self, *args: Any, **kwargs: Any) -> FakeMessage:
        self.sent.append((args, kwargs))
        return FakeMessage()

    def texts(self) -> list[str]:
        return [a[0] for a, _ in self.sent if a]


class FakeStore:
    def __init__(self, data: dict[int, int] | None = None) -> None:
        self.data: dict[int, int] = dict(data or {})

    async def get_all(self) -> dict[int, int]:
        return dict(self.data)

    async def get(self, user_id: int) -> int:
        return self.data.get(user_id, 0)

    async def add(self, user_id: int, amount: int) -> int:
        self.data[user_id] = self.data.get(user_id, 0) + amount
        return self.data[user_id]

    async def remove(self, user_id: int, amount: int) -> int:
        from sorteo_bot.domain.errors import InsufficientEntriesError

        current = self.data.get(user_id, 0)
        if current < amount:
            raise InsufficientEntriesError("sin saldo")
        remaining = current - amount
        if remaining == 0:
            self.data.pop(user_id, None)
        else:
            self.data[user_id] = remaining
        return remaining

    async def remove_user(self, user_id: int) -> bool:
        return self.data.pop(user_id, None) is not None

    async def grant_many(self, user_ids: list[int], amount: int) -> int:
        for uid in user_ids:
            self.data[uid] = self.data.get(uid, 0) + amount
        return len(user_ids)

    async def clear(self) -> None:
        self.data.clear()


def make_settings(**over: Any) -> Settings:
    base: dict[str, Any] = {
        "discord_token": "test-token",
        "draw_reveal_delay_seconds": 0.0,
    }
    base.update(over)
    return Settings(**base)  # type: ignore[arg-type]


def make_bot(store: FakeStore, settings: Settings) -> SimpleNamespace:
    return SimpleNamespace(settings=settings, store=store)


# ---- ParticipacionesAdminCog ----


async def test_registrar_ok() -> None:
    settings = make_settings()
    store = FakeStore()
    cog = ParticipacionesAdminCog(make_bot(store, settings))  # type: ignore[arg-type]
    guild = FakeGuild(members=[FakeMember(1, "Ana")])
    ctx = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.registrar.callback(cog, ctx, "ana", 3)  # type: ignore[attr-defined]
    assert store.data == {1: 3}
    assert any("Ana" in (a[0] if a else "") or "embed" in k for a, k in ctx.sent for k in [k])


async def test_registrar_sin_guild_y_cantidad_invalida() -> None:
    settings = make_settings()
    cog = ParticipacionesAdminCog(make_bot(FakeStore(), settings))  # type: ignore[arg-type]
    ctx = FakeCtx(None)  # type: ignore[arg-type]
    await cog.registrar.callback(cog, ctx, "x", 1)  # type: ignore[attr-defined]
    assert "servidor" in ctx.texts()[0]
    ctx2 = FakeCtx(FakeGuild(members=[FakeMember(1, "Ana")]))  # type: ignore[arg-type]
    await cog.registrar.callback(cog, ctx2, "Ana", 0)  # type: ignore[attr-defined]
    assert "al menos 1" in ctx2.texts()[0]


async def test_registrar_no_encontrado() -> None:
    settings = make_settings()
    cog = ParticipacionesAdminCog(make_bot(FakeStore(), settings))  # type: ignore[arg-type]
    ctx = FakeCtx(FakeGuild(members=[FakeMember(1, "Ana")]))  # type: ignore[arg-type]
    await cog.registrar.callback(cog, ctx, "Zzz Desconocido", 2)  # type: ignore[attr-defined]
    assert "No encuentro" in ctx.texts()[0]


async def test_eliminar_ok_y_sin_saldo() -> None:
    settings = make_settings()
    store = FakeStore({1: 5})
    cog = ParticipacionesAdminCog(make_bot(store, settings))  # type: ignore[arg-type]
    guild = FakeGuild(members=[FakeMember(1, "Ana")])
    ctx = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.eliminar.callback(cog, ctx, "Ana", 2)  # type: ignore[attr-defined]
    assert store.data == {1: 3}
    ctx2 = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.eliminar.callback(cog, ctx2, "Ana", 99)  # type: ignore[attr-defined]
    assert "tantas" in ctx2.texts()[0]


async def test_generar_y_reset() -> None:
    settings = make_settings()
    store = FakeStore()
    cog = ParticipacionesAdminCog(make_bot(store, settings))  # type: ignore[arg-type]
    members = [FakeMember(1, "A"), FakeMember(2, "B"), FakeMember(3, "Bot", bot=True)]
    guild = FakeGuild(members=members, voice_channels=[FakeVoiceChannel("Evento", members)])
    ctx = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.generar.callback(cog, ctx, 1)  # type: ignore[attr-defined]
    assert store.data == {1: 1, 2: 1}
    # sin canal
    ctx_noc = FakeCtx(FakeGuild(members=members, voice_channels=[]))  # type: ignore[arg-type]
    await cog.generar.callback(cog, ctx_noc, 1)  # type: ignore[attr-defined]
    assert "Evento" in ctx_noc.texts()[0]
    # reset
    ctx_r = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.sorteo_eliminar.callback(cog, ctx_r)  # type: ignore[attr-defined]
    assert store.data == {}


# ---- SorteoCog ----


async def test_sorteo_ok_elimina_ganador() -> None:
    settings = make_settings()
    store = FakeStore({1: 10, 2: 1})
    cog = SorteoCog(make_bot(store, settings))  # type: ignore[arg-type]
    members = [FakeMember(1, "Ana"), FakeMember(2, "Beto")]
    guild = FakeGuild(members=members, voice_channels=[FakeVoiceChannel("Sorteo", members)])
    ctx = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.sorteo.callback(cog, ctx)  # type: ignore[attr-defined]
    # un ganador consumido: queda 1 participante
    assert len(store.data) == 1
    assert any("ganador" in t.lower() for t in ctx.texts())


async def test_sorteo_sin_canal_sin_miembros_sin_elegibles() -> None:
    settings = make_settings()
    cog = SorteoCog(make_bot(FakeStore(), settings))  # type: ignore[arg-type]
    ctx_none = FakeCtx(None)  # type: ignore[arg-type]
    await cog.sorteo.callback(cog, ctx_none)  # type: ignore[attr-defined]
    assert "servidor" in ctx_none.texts()[0]

    ctx_noc = FakeCtx(FakeGuild(members=[], voice_channels=[]))  # type: ignore[arg-type]
    await cog.sorteo.callback(cog, ctx_noc)  # type: ignore[attr-defined]
    assert "Sorteo" in ctx_noc.texts()[0]

    guild_empty = FakeGuild(members=[], voice_channels=[FakeVoiceChannel("Sorteo", [])])
    ctx_empty = FakeCtx(guild_empty)  # type: ignore[arg-type]
    await cog.sorteo.callback(cog, ctx_empty)  # type: ignore[attr-defined]
    assert "nadie" in ctx_empty.texts()[0].lower()

    members = [FakeMember(9, "Zed")]
    guild_noe = FakeGuild(members=members, voice_channels=[FakeVoiceChannel("Sorteo", members)])
    ctx_noe = FakeCtx(guild_noe)  # type: ignore[arg-type]
    await cog.sorteo.callback(cog, ctx_noe)  # type: ignore[attr-defined]
    assert "voz no tienen" in ctx_noe.texts()[0]


async def test_unirse_ok_y_sin_canal() -> None:
    settings = make_settings()
    cog = SorteoCog(make_bot(FakeStore(), settings))  # type: ignore[arg-type]
    canal = FakeVoiceChannel("Sorteo", [])
    guild = FakeGuild(members=[], voice_channels=[canal])
    ctx = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.unirse.callback(cog, ctx)  # type: ignore[attr-defined]
    assert canal.connected
    ctx2 = FakeCtx(FakeGuild(members=[], voice_channels=[]))  # type: ignore[arg-type]
    await cog.unirse.callback(cog, ctx2)  # type: ignore[attr-defined]
    assert "Sorteo" in ctx2.texts()[0]


# ---- ConsultaCog ----


async def test_consulta_flujos() -> None:
    settings = make_settings()
    store = FakeStore({2: 4, 1: 2})
    cog = ConsultaCog(make_bot(store, settings))  # type: ignore[arg-type]
    guild = FakeGuild(members=[FakeMember(1, "Ana"), FakeMember(2, "beto")])
    ctx = FakeCtx(guild, author_id=1)  # type: ignore[arg-type]
    await cog.mis_participaciones.callback(cog, ctx)  # type: ignore[attr-defined]
    assert "2" in ctx.texts()[0]

    ctx_p = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.participantes.callback(cog, ctx_p)  # type: ignore[attr-defined]
    assert ctx_p.sent  # embed enviado

    ctx_v = FakeCtx(FakeGuild(members=[]))  # type: ignore[arg-type]
    store_vacia = FakeStore()
    cog_v = ConsultaCog(make_bot(store_vacia, settings))  # type: ignore[arg-type]
    await cog_v.participantes.callback(cog_v, ctx_v)  # type: ignore[attr-defined]
    assert "nadie apuntado" in ctx_v.texts()[0]


async def test_miembros_y_activos() -> None:
    settings = make_settings()
    cog = ConsultaCog(make_bot(FakeStore(), settings))  # type: ignore[arg-type]
    guild = FakeGuild(
        members=[
            FakeMember(1, "Ana", status=discord.Status.online),
            FakeMember(2, "Beto", status=discord.Status.idle),
            FakeMember(3, "Bot", bot=True),
        ]
    )
    ctx = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.miembros.callback(cog, ctx)  # type: ignore[attr-defined]
    assert "Hay 2" in ctx.texts()[0]
    ctx2 = FakeCtx(guild)  # type: ignore[arg-type]
    await cog.usuarios_activos.callback(cog, ctx2)  # type: ignore[attr-defined]
    assert "Conectados" in ctx2.texts()[0]

    ctx_empty = FakeCtx(FakeGuild(members=[]))  # type: ignore[arg-type]
    await cog.miembros.callback(cog, ctx_empty)  # type: ignore[arg-type]
    assert "No veo" in ctx_empty.texts()[0]
    guild_off = FakeGuild(members=[FakeMember(9, "Zed", status=discord.Status.offline)])
    ctx_off = FakeCtx(guild_off)  # type: ignore[arg-type]
    await cog.usuarios_activos.callback(cog, ctx_off)  # type: ignore[attr-defined]
    assert "nadie conectado" in ctx_off.texts()[0]


async def test_consulta_sin_guild() -> None:
    settings = make_settings()
    cog = ConsultaCog(make_bot(FakeStore({1: 1}), settings))  # type: ignore[arg-type]
    for name in ("participantes", "miembros", "usuarios_activos"):
        ctx = FakeCtx(None)  # type: ignore[arg-type]
        await getattr(cog, name).callback(cog, ctx)  # type: ignore[attr-defined]
        assert "servidor" in ctx.texts()[0]
