import argparse
import logging
from importlib import resources
from pathlib import Path

from clisnips.cli.command import Command

logger = logging.getLogger(__name__)


def configure(cmd: argparse.ArgumentParser):
    cmd.add_argument('shell', choices=['bash', 'zsh'])

    return InstallBindingsCommand


class InstallBindingsCommand(Command):
    shell_rcs = {
        'bash': '~/.bashrc',
        'zsh': '~/.zshrc',
    }

    def run(self, argv) -> int:
        shell = argv.shell
        src = resources.files('clisnips.resources').joinpath(f'key-bindings.{shell}')
        dest = f'~/.clisnips.{shell}'
        dest_path = Path(dest).expanduser()
        rc_file = Path(self.shell_rcs[shell]).expanduser()

        logger.info(f'Installing key bindings for {shell} in {dest_path}')
        with src.open() as res:
            with open(dest_path, 'w') as fp:
                fp.write(res.read())

        logger.info(f'Updating {rc_file}')
        with open(rc_file, mode='a') as fp:
            fp.writelines(
                (
                    '# clisnips key bindings',
                    f'[ -f {dest} ] && source {dest}',
                )
            )

        logger.info('OK', extra={'color': 'success'})
        self.print(
            ('info', 'To use the new key bindings, either open a new shell or run:'),
            ('default', f'source {rc_file}'),
            sep='\n',
            stderr=True,
        )

        return 0
