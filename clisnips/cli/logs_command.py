import argparse
import asyncio
import logging
import pickle
import struct
import sys
from logging import LogRecord
from pathlib import Path

from .command import Command
from .utils import UrwidMarkupHelper


class RecordFormatter(logging.Formatter):
    levels = {
        'DEBUG': 'debug',
        'INFO': 'info',
        'WARNING': 'warning',
        'ERROR': 'error',
        'CRITICAL': 'error',
    }

    def __init__(self, printer: UrwidMarkupHelper) -> None:
        self._printer = printer
        super().__init__()

    def formatMessage(self, record: LogRecord) -> str:
        spec = self.levels.get(record.levelname, 'default')
        markup = [
            (spec, f'{record.levelname} '),
            ('default', '['),
            ('accent', record.name),
            ('default', ']'),
            *self._call_site(record),
            ('default', f': {record.message}'),
        ]
        return self._printer.convert_markup(markup, sys.stdout.isatty())

    def _call_site(self, record: LogRecord):
        return (
            ('default', '['),
            ('debug', record.funcName),
            ('default', ':'),
            ('debug', str(record.lineno)),
            ('default', ']'),
        )


class Server:
    def __init__(self, log_file: Path, printer: UrwidMarkupHelper) -> None:
        self._log_file = log_file
        self._formatter = RecordFormatter(printer)
        self._print = printer.print

    async def start(self):
        self._print(('info', f'>>> starting log server on {self._log_file}'))
        server = await asyncio.start_unix_server(self._client_connected, self._log_file)
        async with server:
            await server.serve_forever()

    async def _client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._print(('success', '>>> client logger connected'))
        try:
            while record := await self._read_record(reader):
                self._handle_record(record)
            self._print(('info', '>>> client logger disconnected'))
        finally:
            writer.close()

    async def _read_record(self, reader: asyncio.StreamReader) -> logging.LogRecord | None:
        header = await reader.read(4)
        if not header:
            return
        record_len, *_ = struct.unpack('>L', header)
        buf = await reader.readexactly(record_len)
        return logging.makeLogRecord(pickle.loads(buf))

    def _handle_record(self, record: logging.LogRecord):
        print(self._formatter.format(record))


class LogsCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        action.add_parser('logs', help='Watch clisnips logs')

    def run(self, argv) -> int:
        log_file = self.container.config.log_file

        async def serve():
            server = Server(log_file, self.container.markup_helper)
            task = asyncio.create_task(server.start())
            await asyncio.gather(task)

        try:
            asyncio.run(serve(), debug=False)
        except (KeyboardInterrupt, SystemExit):
            ...

        return 0
