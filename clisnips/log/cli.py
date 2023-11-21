import logging
import sys
from typing import IO

from clisnips.cli.utils import UrwidMarkupHelper


def configure(helper: UrwidMarkupHelper, level: str, stream: IO = sys.stderr):
    handler = logging.StreamHandler(stream)
    if stream.isatty():
        handler.formatter = UrwidRecordFormatter(helper)
    logging.basicConfig(level=level.upper(), handlers=(handler,))


class UrwidRecordFormatter(logging.Formatter):
    levels = {
        'DEBUG': 'debug',
        'INFO': 'info',
        'SUCCESS': 'success',
        'WARN': 'warning',
        'WARNING': 'warning',
        'ERROR': 'error',
        'CRITICAL': 'error',
    }

    def __init__(self, helper: UrwidMarkupHelper) -> None:
        self._helper = helper
        super().__init__()

    def formatMessage(self, record: logging.LogRecord):
        spec = self.levels.get(record.levelname, 'info')
        markup = [
            (spec, record.levelname),
            ('default', ': '),
            (getattr(record, 'color', spec), record.message),
            ('default', ''),
        ]
        return self._helper.convert_markup(markup, tty=True)
