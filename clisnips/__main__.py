import logging
import sys

from clisnips.cli import Application
from clisnips.config.paths import ensure_app_dirs, get_state_path, xdg_state_home


def main():
    ensure_app_dirs()
    log_file = get_state_path('clisnips.log')
    # TODO: allow config to set the logging level
    logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode='w')

    app = Application()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
