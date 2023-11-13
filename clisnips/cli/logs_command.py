
import argparse
import asyncio
from pathlib import Path
import pickle
import struct

from .command import Command


class Server:
    def __init__(self, log_file: Path) -> None:
        self._log_file = log_file

    async def start(self):
        print(f'>>> starting server on {self._log_file}')
        server = await asyncio.start_unix_server(self._client_connected, self._log_file)
        async with server:
            await server.serve_forever()

    async def _client_connected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        print('>>> client connected')
        try:
            while True:
                await self._read_record(reader)
        finally:
            writer.close()

    async def _read_record(self, reader: asyncio.StreamReader):
        header = await reader.read(4)
        record_len, *_ = struct.unpack('>L', header)
        buf = await reader.readexactly(record_len)
        record = pickle.loads(buf)
        print(record)


class LogsCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        action.add_parser('logs', help='Watch clisnips logs')

    def run(self, argv) -> int | None:
        log_file = self.container.config.log_file

        async def serve():
            server = Server(log_file)
            task = asyncio.create_task(server.start())
            await asyncio.gather(task)

        try:
            asyncio.run(serve(), debug=True)
        except (KeyboardInterrupt, SystemExit):
            ...

        return 0
