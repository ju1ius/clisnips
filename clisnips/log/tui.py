import logging
from pathlib import Path


def configure(log_file: Path, level: str | None = None):
    match level:
        case None | '':
            logging.basicConfig(handlers=(logging.NullHandler(),))
        case _:
            from logging.handlers import SocketHandler

            handler = SocketHandler(str(log_file), None)
            logging.basicConfig(level=level.upper(), handlers=(handler,))
