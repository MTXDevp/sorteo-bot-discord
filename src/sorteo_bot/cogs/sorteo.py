# mypy: disable-error-code="arg-type"
import asyncio
import logging
import random
from typing import Any

import discord
from discord.ext import commands

from sorteo_bot.domain.draw import choose_weighted_winner, probabilities
from sorteo_bot.domain.errors import NoParticipantsError
from sorteo_bot.utils.discord_display import display_name_of

log = logging.getLogger(__name__)


def _find_voice_channel(
    channels: list[discord.VoiceChannel], *names: str
) -> discord.VoiceChannel | None:
    wanted = {n.casefold() for n in names}
    return next((c for c in channels if c.name.casefold() in wanted), None)


class SorteoCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: Any = bot

    @commands.hybrid_command(name="sorteo", description="Sortear entre los que están en voz.")
    @commands.has_permissions(administrator=True)
    async def sorteo(self, ctx: commands.Context[Any]) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        canal = _find_voice_channel(
            guild.voice_channels, self.bot.settings.voice_channel_sorteo, "sorteo"
        )
        if canal is None:
            await ctx.send("No veo el canal de voz Sorteo.")
            return
        if not canal.members:
            await ctx.send("No hay nadie en el canal Sorteo.")
            return

        saldos = await self.bot.store.get_all()
        elegibles = {m.id: saldos[m.id] for m in canal.members if m.id in saldos}
        if not elegibles:
            await ctx.send("Los que están en voz no tienen participaciones.")
            return

        try:
            probs = probabilities(elegibles)
        except NoParticipantsError:
            await ctx.send("Al final no hay a quién sortear.")
            return

        lines = []
        for user_id, entries in sorted(elegibles.items(), key=lambda kv: kv[1], reverse=True):
            member = guild.get_member(user_id)
            shown = display_name_of(member) if member else f"ID {user_id}"
            lines.append(f"- **{shown}**: {entries} ({probs[user_id] * 100:.1f}%)")
        await ctx.send(
            embed=discord.Embed(
                title="Sorteo",
                description="Los que entran y su peso:\n" + "\n".join(lines),
                color=discord.Color.gold(),
            )
        )

        teaser = await ctx.send("Girando... 🎰")
        await asyncio.sleep(self.bot.settings.draw_reveal_delay_seconds)

        ganador_id = choose_weighted_winner(elegibles, rng=random.Random())
        ganador = guild.get_member(ganador_id)
        shown = display_name_of(ganador) if ganador else f"ID {ganador_id}"
        try:
            await teaser.delete()
        except discord.HTTPException:
            log.debug("no pude borrar el mensaje de girando", exc_info=True)
        await ctx.send(f"Ganador: **{shown}** 🎉")
        await self.bot.store.remove_user(ganador_id)
        await ctx.send(f"quito a **{shown}** de la lista para el próximo.")
        log.info("sorteo ganado por %s con %d", shown, elegibles[ganador_id])

    @commands.hybrid_command(name="unirse", description="Meter al bot en el canal Sorteo.")
    async def unirse(self, ctx: commands.Context[Any]) -> None:
        guild = ctx.guild
        if guild is None:
            await ctx.send("Esto solo funciona dentro de un servidor.")
            return
        canal = _find_voice_channel(
            guild.voice_channels, self.bot.settings.voice_channel_sorteo, "sorteo"
        )
        if canal is None:
            await ctx.send("No veo el canal de voz Sorteo.")
            return
        voice = ctx.guild.voice_client if ctx.guild else None
        if isinstance(voice, discord.VoiceClient) and voice.is_connected():
            await voice.move_to(canal)
        else:
            await canal.connect()
        await ctx.send(f"Me meto en **{canal.name}**.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SorteoCog(bot))
