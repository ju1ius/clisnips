import shutil
from pathlib import Path
from typing import Optional

from .command import Command

__dir__ = Path(__file__).absolute().parent


class InstallShellKeyBindingsCommand(Command):

    shell_rcs = {
        'bash': '~/.bashrc',
        'zsh': '~/.zshrc',
    }

    def run(self, argv) -> Optional[int]:
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
