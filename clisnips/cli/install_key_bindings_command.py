import argparse
import logging
import shutil
from pathlib import Path

from .command import Command

__dir__ = Path(__file__).absolute().parent
logger = logging.getLogger(__name__)


class InstallShellKeyBindingsCommand(Command):

    shell_rcs = {
        'bash': '~/.bashrc',
        'zsh': '~/.zshrc',
    }

    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('key-bindings', help='Installs clisnips key bindings for the given shell.')
        cmd.add_argument('shell', choices=['bash', 'zsh'])

    def run(self, argv) -> int:
        shell = argv.shell
        bindings_src = __dir__ / 'shell' / f'key-bindings.{shell}'
        bindings_dst = Path(f'~/.clisnips.{shell}').expanduser()

        logger.info(f'Installing key bindings for {shell} in {bindings_dst}')
        shutil.copy(bindings_src, bindings_dst)

        rc_file = Path(self.shell_rcs[shell]).expanduser()
        with open(rc_file, mode='a') as fp:
            logger.info(f'Updating {rc_file}')
            fp.writelines([
                '# clisnips key bindings\n',
                f'source {bindings_dst}\n',
            ])

        logger.info('OK', extra={'color': 'success'})
        self.print(
            ('info', 'To use the new key bindings, either open a new shell or run:'),
            ('default', f'source {rc_file}'),
            sep='\n',
            stderr=True,
        )

        return 0
