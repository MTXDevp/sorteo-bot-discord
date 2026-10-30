# mypy: disable-error-code="arg-type"
import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from sorteo_bot.domain.errors import InsufficientEntriesError, InvalidEntriesError
from sorteo_bot.services.member_resolver import resolve_member_id

log = logging.getLogger(__name__)


def _find_voice_channel(
    channels: list[discord.VoiceChannel], base_name: str
) -> discord.VoiceChannel | None:
    wanted = base_name.casefold()
    return next((c for c in channels if c.name.casefold() == wanted), None)


class ParticipacionesAdminCog(commands.Cog):
    # Todo lo que toca saldo es solo para admins. Lo demás está en ConsultaCog.
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: Any = bot

    @commands.hybrid_command(name="registrar", description="Apuntar a alguien al sorteo.")
    @app_commands.describe(nombre="Nombre en el servidor", participaciones="Cuántas suma")
    @commands.has_permissions(administrator=True)
    async def registrar(
        self, ctx: commands.Context[Any], nombre: str, participaciones: int
    ) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        if participaciones <= 0:
            await ctx.send("Tiene que ser al menos 1 participación.")
            return
        member_id = resolve_member_id(
            guild.members, nombre, threshold=self.bot.settings.fuzzy_threshold
        )
        if member_id is None:
            await ctx.send(f"No encuentro a **{nombre}** en el servidor.")
            return
        try:
            total = await self.bot.store.add(member_id, participaciones)
        except InvalidEntriesError as exc:
            await ctx.send(f"No me vale: {exc}")
            return
        member = guild.get_member(member_id)
        shown = member.display_name if member else nombre
        log.info("%s apunta a %s (+%d, total %d)", ctx.author, shown, participaciones, total)
        await ctx.send(
            embed=discord.Embed(
                title="Apuntado",
                description=f"**{shown}** lleva {total} participaciones. Suerte 🍀",
                color=discord.Color.green(),
            )
        )

    @commands.hybrid_command(name="eliminar", description="Quitar participaciones a alguien.")
    @app_commands.describe(nombre="Nombre en el servidor", participaciones="Cuántas quita")
    @commands.has_permissions(administrator=True)
    async def eliminar(self, ctx: commands.Context[Any], nombre: str, participaciones: int) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        if participaciones <= 0:
            await ctx.send("Tiene que ser al menos 1.")
            return
        member_id = resolve_member_id(
            guild.members, nombre, threshold=self.bot.settings.fuzzy_threshold
        )
        if member_id is None:
            await ctx.send(f"No encuentro a **{nombre}**.")
            return
        try:
            remaining = await self.bot.store.remove(member_id, participaciones)
        except InsufficientEntriesError:
            await ctx.send("No tiene tantas para quitarle.")
            return
        member = guild.get_member(member_id)
        shown = member.display_name if member else nombre
        await ctx.send(f"**{shown}** se queda con {remaining}.")

    @commands.hybrid_command(
        name="generar", description="Dar 1 participación a los que están en el canal del evento."
    )
    @app_commands.describe(cantidad="Cuántas da a cada uno (normalmente 1)")
    @commands.has_permissions(administrator=True)
    async def generar(self, ctx: commands.Context[Any], cantidad: int = 1) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        if cantidad <= 0:
            await ctx.send("Tiene que ser al menos 1.")
            return
        canal = _find_voice_channel(
            guild.voice_channels, self.bot.settings.voice_channel_evento
        ) or _find_voice_channel(guild.voice_channels, "evento")
        if canal is None:
            await ctx.send("No veo ningún canal de voz llamado Evento.")
            return
        ids = [m.id for m in canal.members if not m.bot]
        if not ids:
            await ctx.send(f"En **{canal.name}** no hay nadie ahora mismo.")
            return
        await self.bot.store.grant_many(ids, cantidad)
        log.info("%s da +%d a %d de '%s'", ctx.author, cantidad, len(ids), canal.name)
        await ctx.send(f"+{cantidad} para {len(ids)} personas de **{canal.name}**.")

    @commands.hybrid_command(name="sorteo_eliminar", description="Borrarlo todo y empezar de cero.")
    @commands.has_permissions(administrator=True)
    async def sorteo_eliminar(self, ctx: commands.Context[Any]) -> None:
        await self.bot.store.clear()
        log.warning("Reset total pedido por %s", ctx.author)
        await ctx.send("Borradas todas las participaciones.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ParticipacionesAdminCog(bot))
