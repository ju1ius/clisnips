import importlib
from argparse import ArgumentParser, Namespace
from collections.abc import Callable
from typing import Self

from .command import Command


class LazySubParser(ArgumentParser):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._initialized = False

    def parse_known_args(self, args: list[str], namespace: Namespace) -> tuple[Namespace, list[str]]:
        if not self._initialized:
            self._initialized = True
            self._load_command(self._defaults['__module__'])

        return super().parse_known_args(args, namespace)

    def _load_command(self, mod: str):
        module = importlib.import_module(f'clisnips.cli.commands.{mod}')
        configure: Callable[[Self], type[Command]] = getattr(module, 'configure')
        self._defaults['__command__'] = configure(self)
