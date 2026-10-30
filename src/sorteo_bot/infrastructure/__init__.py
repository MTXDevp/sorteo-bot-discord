"""Persistencia SQLite con contrato Repository (testeable y sustituible)."""

from sorteo_bot.infrastructure.store import (
    ParticipationRepository,
    SqliteParticipationStore,
)

__all__ = ["ParticipationRepository", "SqliteParticipationStore"]
