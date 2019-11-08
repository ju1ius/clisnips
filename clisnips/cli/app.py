import sys
from argparse import ArgumentParser, FileType

from clisnips.dic import DependencyInjectionContainer
from .config_command import ShowConfigCommand
from .dump_command import DumpCommand
from .export_command import ExportCommand
from .import_command import ImportCommand
from .optimize_command import OptimizeCommand


class Application:

    commands = {
        'import': ImportCommand,
        'export': ExportCommand,
        'optimize': OptimizeCommand,
        'dump': DumpCommand,
        'config': ShowConfigCommand,
    }

    def run(self) -> int:
        argv = self._parse_arguments()
        try:
            cls = self.commands[argv.command]
        except KeyError:
            return self._run_tui(argv)
        return self._run_command(cls, argv)

    @staticmethod
    def _parse_arguments():
        parser = ArgumentParser(
            prog='clisnips',
            description='A command-line snippets manager.',
        )
        parser.add_argument('--database', help='Path to an alternate SQLite database.')

        sub_parsers = parser.add_subparsers(title='Subcommands', dest='command',
                                            description='The following commands are available outside the GUI.')

        import_cmd = sub_parsers.add_parser('import', help='Imports snippets from a file.')
        import_cmd.add_argument('--format', choices=['xml', 'cli-companion'], default='xml')
        import_cmd.add_argument('--replace', action='store_true', help='Replaces snippets. The default is to append.')
        import_cmd.add_argument('file', type=FileType('r'))
        #
        export_cmd = sub_parsers.add_parser('export', help='Exports snippets to XML.')
        export_cmd.add_argument('file', type=FileType('w'))
        #
        dump_cmd = sub_parsers.add_parser('dump', help='Runs a SQL dump of the database.')
        dump_cmd.add_argument('file', type=FileType('w'), default=sys.stdout)
        #
        optimize_cmd = sub_parsers.add_parser('optimize', help='Runs optimization tasks on the database.')
        optimize_cmd.add_argument('--rebuild', action='store_true', help='Rebuilds the search index before optimizing.')
        #
        config_cmd = sub_parsers.add_parser('config', help='Shows the current configuration.')

        return parser.parse_args()

    def _run_command(self, cls, argv) -> int:
        dic = DependencyInjectionContainer(argv.database)
        command = cls(dic)
        try:
            ret_code = command.run(argv)
            return ret_code if ret_code is not None else 0
        except Exception as err:
            self._print_exception(err)
            return 128

    @staticmethod
    def _run_tui(argv) -> int:
        from clisnips.tui.app import Application
        dic = DependencyInjectionContainer(argv.database)
        app = Application(dic)
        return app.run()

    def _print_exception(self, err: Exception):
        from traceback import format_exc
        from clisnips.cli.utils import UrwidMarkupHelper
        helper = UrwidMarkupHelper()
        msg = f'{err}\n{format_exc()}'
        output = helper.convert_markup(('error', msg), tty=True)
        print(output, file=sys.stderr)
