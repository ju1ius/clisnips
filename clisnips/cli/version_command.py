import argparse

from clisnips import __version__

from .command import Command


class VersionCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        action.add_parser('version', help='Outputs the clisnips version number.')

    def run(self, argv) -> int:
        print(__version__)
        return 0
