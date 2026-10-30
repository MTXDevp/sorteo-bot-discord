import logging
from typing import Any

import discord
from discord.ext import commands

from sorteo_bot.config import Settings
from sorteo_bot.infrastructure.store import ParticipationRepository

log = logging.getLogger(__name__)


class SorteoBot(commands.Bot):
    def __init__(self, settings: Settings, store: ParticipationRepository) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        # message_content solo por los comandos con !, los slash no lo necesitan
        intents.message_content = True
        super().__init__(command_prefix=settings.command_prefix, intents=intents)
        self.settings = settings
        self.store = store

    async def setup_hook(self) -> None:
        from sorteo_bot.cogs.consulta import ConsultaCog
        from sorteo_bot.cogs.participaciones import ParticipacionesAdminCog
        from sorteo_bot.cogs.sorteo import SorteoCog

        await self.add_cog(ParticipacionesAdminCog(self))
        await self.add_cog(SorteoCog(self))
        await self.add_cog(ConsultaCog(self))
        try:
            synced = await self.tree.sync()
            log.info("Slash commands sincronizados: %d", len(synced))
        except discord.HTTPException:
            log.exception("No se pudieron sincronizar los slash commands")

    async def on_ready(self) -> None:
        user = self.user
        log.info("Conectado como %s (id=%s)", user, user.id if user else "?")

    async def on_command_error(
        self, ctx: commands.Context[Any], error: commands.CommandError
    ) -> None:
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Ese comando no existe, revisa el nombre.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Falta el argumento `{error.param.name}`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Ese argumento no me vale, revisa el formato.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Esto es solo para administradores.")
        else:
            log.error("Error en comando", exc_info=error)
            await ctx.send(f"Algo falló: `{type(error).__name__}`")

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        from discord import app_commands

        if isinstance(error, app_commands.MissingPermissions):
            message = "Esto es solo para administradores."
        elif isinstance(error, app_commands.CommandOnCooldown):
            message = f"Espera {error.retry_after:.0f}s antes de repetirlo."
        else:
            log.error("Error en slash command", exc_info=error)
            message = f"Algo falló: `{type(error).__name__}`"
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            log.exception("No pude avisar del error del slash")
