import argparse
import shutil
from pathlib import Path

from .command import Command

__dir__ = Path(__file__).absolute().parent


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
        self.print(('info', f'Installing key bindings for {shell}...'))
        bindings_src = __dir__ / 'shell' / f'key-bindings.{shell}'
        bindings_dst = Path(f'~/.clisnips.{shell}').expanduser()
        shutil.copy(bindings_src, bindings_dst)
        rc_file = Path(self.shell_rcs[shell]).expanduser()
        with open(rc_file, mode='a') as fp:
            fp.writelines([
                '# clisnips key bindings\n',
                f'source {bindings_dst}\n',
            ])

        self.print(
            ('success', 'Done !'),
            ('info', 'To use the new key bindings, either open a new shell or run:'),
            ('warning', f'$ source {rc_file}'),
            sep='\n'
        )

        return 0
