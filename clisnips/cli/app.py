import argparse
import logging
import sys
from typing import Any

from clisnips.dic import DependencyInjectionContainer

from .command import Command
from .parser import LazySubParser

logger = logging.getLogger(__name__)


class Application:
    commands: dict[str, dict[str, Any]] = {
        'version': {
            'help': 'Outputs the clisnips version number.',
        },
        'config': {
            'help': 'Shows the current configuration.',
        },
        'key-bindings': {
            'help': 'Installs clisnips key bindings for the given shell.',
            'module': 'install_key_bindings',
        },
        'import': {
            'help': 'Imports snippets from a file.',
            'module': '_import',
        },
        'export': {
            'help': 'Exports snippets to a file.',
        },
        'dump': {
            'help': 'Runs a SQL dump of the database.',
        },
        'optimize': {
            'help': 'Runs optimization tasks on the database.',
        },
        'logs': {
            'help': 'Watch clisnips TUI logs',
        },
    }

    def run(self) -> int:
        argv = self._parse_arguments()
        if cls := getattr(argv, '__command__', None):
            return self._run_command(cls, argv)
        return self._run_tui(argv)

    @classmethod
    def _parse_arguments(cls):
        parser = argparse.ArgumentParser(
            prog='clisnips',
            description='A command-line snippets manager.',
        )
        parser.add_argument('--database', help='Path to an alternate SQLite database.')
        parser.add_argument('--log-level', choices=('debug', 'info', 'warning', 'error'), help='')
        sub = parser.add_subparsers(
            title='Subcommands',
            metavar='command',
            description='The following commands are available outside the GUI.',
            parser_class=LazySubParser,
        )
        for name, kwargs in cls.commands.items():
            module = kwargs.pop('module', name)
            p = sub.add_parser(name, **kwargs)
            p.set_defaults(__module__=module)

        return parser.parse_args()

    def _run_command(self, cls: type[Command], argv) -> int:
        from clisnips.log.cli import configure as configure_logging

        dic = self._create_container(argv)
        configure_logging(dic.markup_helper, argv.log_level or 'info', sys.stderr)

        logger.debug('launching command: %s', argv)
        command = cls(dic)
        try:
            return command.run(argv)
        except Exception as err:
            logger.exception(err)
            return 128

    def _run_tui(self, argv) -> int:
        from clisnips.log.tui import configure as configure_logging
        from clisnips.tui.app import Application

        dic = self._create_container(argv)
        configure_logging(dic.config.log_file, argv.log_level)

        logging.getLogger(__name__).info('launching TUI')
        app = Application(dic)
        return app.run()

    @staticmethod
    def _create_container(argv) -> DependencyInjectionContainer:
        return DependencyInjectionContainer(database=argv.database)
