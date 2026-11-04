# Sorteo Bot

Bot de Discord para sorteos ponderados por participaciones.

## Funcionalidades

- Sorteo ponderado: la probabilidad es proporcional al número de participaciones. El porcentaje de cada participante se muestra antes del sorteo.
- Comandos disponibles con prefijos `/` y `!`: `registrar`, `eliminar`, `generar`, `sorteo`, `sorteo_eliminar`, `unirse`, `mis_participaciones`, `participantes`, `miembros`, `usuarios_activos`.
- Resolución de nombres por coincidencia aproximada. Ejemplo: "jose" resuelve a "José García".
- Permisos: la gestión de saldo es solo para administradores. Consulta y participación, abiertas al resto.
- Migración automática de `participaciones.json` a SQLite en el primer arranque.

## Instalación

    pip install -e ".[dev]"
    cp .env.example .env
    python -m sorteo_bot

1. Crear la aplicación en https://discord.com/developers/applications
2. Activar los intents `Members`, `Presence` y `Message Content`.
3. Invitar al bot con los scopes `bot` y `applications.commands`.
4. Definir `DISCORD_TOKEN` en `.env`.

Con Docker:

    docker build -t sorteo-bot .
    docker run --env-file .env -v ./data:/app/data sorteo-bot

Variables de entorno (ver `.env.example`): `DISCORD_TOKEN`, `COMMAND_PREFIX`, `VOICE_CHANNEL_SORTEO`, `VOICE_CHANNEL_EVENTO`, `SQLITE_PATH`, `FUZZY_THRESHOLD`.

## Estructura

    src/sorteo_bot/
      bot.py, main.py
      config.py
      domain/
      services/
      infrastructure/
      cogs/
    tests/

- Cálculo del sorteo en `choose_weighted_winner`, sin dependencias de Discord.
- Persistencia definida por `Protocol`. En tests se usa implementación en memoria.
- Los cogs validan la entrada, acceden al store y devuelven la respuesta.

## Calidad

    pytest
    ruff check src tests && ruff format --check src tests
    mypy src/sorteo_bot

Cobertura mínima exigida: 80%. CI con GitHub Actions en Python 3.11 a 3.13.

## Pendiente

- Programación de sorteos y múltiples premios por noche.
- Evaluación de Postgres cuando SQLite sea insuficiente.
- Historial de ganadores para auditoría.
