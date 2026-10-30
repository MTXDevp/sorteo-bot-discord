import asyncio
import logging

from sorteo_bot.bot import SorteoBot
from sorteo_bot.config import get_settings
from sorteo_bot.infrastructure.store import SqliteParticipationStore
from sorteo_bot.logging_config import configure_logging

log = logging.getLogger(__name__)


async def amain() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    token = settings.discord_token.strip()
    if not token or token == "pon-tu-token-aqui":
        raise SystemExit("Falta DISCORD_TOKEN. Copia .env.example a .env y pon el tuyo.")

    store = SqliteParticipationStore(settings.resolved_sqlite_path)
    await store.initialize()
    migrated = await store.import_legacy_json(settings.legacy_json_path)
    if migrated:
        log.info("Me traje %d usuarios del JSON viejo.", migrated)

    bot = SorteoBot(settings, store)
    async with bot:
        await bot.start(token)


def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        log.info("Cerrando, hasta luego.")
