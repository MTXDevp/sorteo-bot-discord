# mypy: disable-error-code="arg-type"
import logging
from typing import Any

import discord
from discord.ext import commands

from sorteo_bot.utils.discord_display import display_name_of

log = logging.getLogger(__name__)

_STATUS_ICON = {
    discord.Status.online: "🟢",
    discord.Status.idle: "🟡",
    discord.Status.dnd: "🔴",
    discord.Status.offline: "⚫",
}


class ConsultaCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: Any = bot

    @commands.hybrid_command(name="mis_participaciones", description="Mirar cuántas llevas.")
    async def mis_participaciones(self, ctx: commands.Context[Any]) -> None:
        total = await self.bot.store.get(ctx.author.id)
        if total:
            await ctx.send(f"Llevas **{total}**.")
        else:
            await ctx.send("Todavía no tienes ninguna.")

    @commands.hybrid_command(name="participantes", description="Ver quién está apuntado.")
    async def participantes(self, ctx: commands.Context[Any]) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        saldos = await self.bot.store.get_all()
        if not saldos:
            await ctx.send("Aún no hay nadie apuntado.")
            return
        rows: list[tuple[str, int]] = []
        for user_id, entries in saldos.items():
            member = guild.get_member(user_id)
            if member is not None:
                rows.append((display_name_of(member), entries))
        if not rows:
            await ctx.send("Los apuntados ya no están en el servidor.")
            return
        rows.sort(key=lambda r: r[0].casefold())
        body = "\n".join(f"- **{name}**: {entries}" for name, entries in rows)
        await ctx.send(
            embed=discord.Embed(
                title=f"Apuntados ({len(rows)})",
                description=body[:4000],
                color=discord.Color.blurple(),
            )
        )

    @commands.hybrid_command(name="miembros", description="Listar la gente del servidor.")
    @commands.has_permissions(administrator=True)
    async def miembros(self, ctx: commands.Context[Any]) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        names = sorted(
            (display_name_of(m) for m in guild.members if not m.bot),
            key=str.casefold,
        )
        if not names:
            await ctx.send("No veo a nadie.")
            return
        # Los mensajes de discord cortan a los 2000 caracteres, lo troceo a mano
        chunk, chunks = "", []
        for name in names:
            if len(chunk) + len(name) + 1 > 1800:
                chunks.append(chunk)
                chunk = ""
            chunk += name + "\n"
        if chunk:
            chunks.append(chunk)
        await ctx.send(f"Hay {len(names)}:\n{chunks[0]}")
        for extra in chunks[1:4]:
            await ctx.send(extra)

    @commands.hybrid_command(name="usuarios_activos", description="Ver quién anda por aquí.")
    @commands.has_permissions(administrator=True)
    async def usuarios_activos(self, ctx: commands.Context[Any]) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        activos = [
            f"{_STATUS_ICON.get(m.status, '⚪')} {display_name_of(m)}"
            for m in guild.members
            if not m.bot
            and m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
        ]
        if not activos:
            await ctx.send("No hay nadie conectado ahora.")
            return
        await ctx.send("Conectados:\n" + "\n".join(sorted(activos, key=str.casefold))[:1900])


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ConsultaCog(bot))
