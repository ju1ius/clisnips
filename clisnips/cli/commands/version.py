import argparse

from clisnips import __version__

from ..command import Command


def configure(parser: argparse.ArgumentParser):
    return VersionCommand


class VersionCommand(Command):
    def run(self, argv) -> int:
        print(__version__)
        return 0
