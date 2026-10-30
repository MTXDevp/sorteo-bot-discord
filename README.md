# Sorteo Bot para Discord

Empecé con un `sorteo.py` de 400 líneas todo mezclado y lo fui rompiendo en piezas
hasta dejarlo en algo que se puede enseñar: sorteo ponderado de verdad, comandos
slash + prefijo `!`, y SQLite en vez del JSON que se corrompía a la mínima.

No es un framework ni pretende serlo, es el bot que uso en mi servidor para los
sorteos y me sirve para practicar Python en serio (tipos, tests, CI).

## Qué hace

- Sorteo con peso: quien tiene más participaciones tiene más probabilidad. Se ve
  el porcentaje de cada uno antes de girar.
- Comandos híbridos, valen con `/` y con `!`: `registrar`, `eliminar`, `generar`,
  `sorteo`, `sorteo_eliminar`, `unirse`, `mis_participaciones`, `participantes`,
  `miembros`, `usuarios_activos`.
- Para apuntar acepta el nombre aproximado ("jose" encuentra a "José García").
- Solo los admins tocan el saldo. El resto puede consultar y jugar.
- Migra solo el `participaciones.json` viejo a SQLite la primera vez.

## Ponerlo en marcha

```bash
pip install -e ".[dev]"
cp .env.example .env   # pon ahí tu DISCORD_TOKEN
python -m sorteo_bot
```

Lo del token: https://discord.com/developers/applications, activas los intents
de Members, Presence y Message Content, e invitas al bot con `bot` +
`applications.commands`.

Con Docker:

```bash
docker build -t sorteo-bot .
docker run --env-file .env -v ./data:/app/data sorteo-bot
```

Variables que uso (ver `.env.example`): `DISCORD_TOKEN`, `COMMAND_PREFIX` (!),
`VOICE_CHANNEL_SORTEO` (Sorteo), `VOICE_CHANNEL_EVENTO` (Evento),
`SQLITE_PATH` (data/sorteo.db), `FUZZY_THRESHOLD` (70).

## Cómo está organizado

```
src/sorteo_bot/
  bot.py, main.py      # arranque
  config.py            # settings con pydantic
  domain/              # draw.py y modelos, sin discord ni disco
  services/            # resolver de nombres
  infrastructure/      # sqlite
  cogs/                # los comandos, en tres grupos
tests/
```

Separé el cálculo del sorteo (`choose_weighted_winner`) para poder testearlo
sin montar Discord, y la persistencia va detrás de un Protocol así que en los
tests uso un fake en memoria. Los cogs son finos a posta: validan, llaman al
store y responden.

## Calidad

```bash
pytest            # 39 tests, pide 80% de cobertura
ruff check src tests && ruff format --check src tests
mypy src/sorteo_bot   # strict
```

Hay workflow de GitHub Actions con python 3.11 a 3.13 que pasa esas tres cosas.

## Pendiente

- Programar sorteos y que haya varios premios por noche.
- Probarlo con Postgres cuando el SQLite se quede corto.
- Guardar un historial de ganadores para auditar.

MIT.
