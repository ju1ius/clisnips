import argparse
import logging
import sys

from clisnips.dic import DependencyInjectionContainer

from .command import Command
from .config_command import ShowConfigCommand
from .dump_command import DumpCommand
from .export_command import ExportCommand
from .import_command import ImportCommand
from .install_key_bindings_command import InstallShellKeyBindingsCommand
from .logs_command import LogsCommand
from .optimize_command import OptimizeCommand


class Application:

    commands: dict[str, type[Command]] = {
        'import': ImportCommand,
        'export': ExportCommand,
        'optimize': OptimizeCommand,
        'dump': DumpCommand,
        'config': ShowConfigCommand,
        'key-bindings': InstallShellKeyBindingsCommand,
        'logs': LogsCommand,
    }

    def run(self) -> int:
        argv = self._parse_arguments()
        if cls := self.commands.get(argv.command):
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

        sub_parsers = parser.add_subparsers(
            title='Subcommands',
            dest='command',
            description='The following commands are available outside the GUI.',
        )
        for _, cmd in cls.commands.items():
            cmd.configure(sub_parsers) # type: ignore

        return parser.parse_args()

    def _run_command(self, cls: type[Command], argv) -> int:
        dic = self._create_container(argv)
        logging.getLogger(__name__).info('launching command: %s', argv)
        command = cls(dic)
        try:
            return command.run(argv)
        except Exception as err:
            self._print_exception(err)
            return 128

    def _run_tui(self, argv) -> int:
        from clisnips.tui.app import Application
        dic = self._create_container(argv)
        logging.getLogger(__name__).info('launching TUI')
        app = Application(dic)
        return app.run()

    @staticmethod
    def _create_container(argv) -> DependencyInjectionContainer:
        return DependencyInjectionContainer(
            database=argv.database,
            log_level=argv.log_level,
        )

    def _print_exception(self, err: Exception):
        from traceback import format_exc

        from clisnips.cli.utils import UrwidMarkupHelper
        helper = UrwidMarkupHelper()
        markup = [
            ('error', str(err)),
            ('default', f'\n{format_exc()}'),
        ]
        output = helper.convert_markup(markup, tty=sys.stderr.isatty())
        print(output, file=sys.stderr)
