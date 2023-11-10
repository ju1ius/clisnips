import logging
import sys

from clisnips.cli import Application
from clisnips.config import xdg_state_home


def main():
    log_file = xdg_state_home() / 'clisnips' / 'clisnips.log'
    log_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    # TODO: allow config to set the logging level
    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='w')

    app = Application()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
