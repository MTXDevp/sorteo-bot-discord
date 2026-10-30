import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(level.upper())
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.setLevel(level.upper())
    root.addHandler(handler)

    # discord.py en DEBUG es insoportable, lo bajo salvo que lo pidas a posta
    if level.upper() != "DEBUG":
        logging.getLogger("discord").setLevel(logging.WARNING)
