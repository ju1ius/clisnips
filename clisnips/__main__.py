import sys

from clisnips.cli import Application
from clisnips.config.paths import ensure_app_dirs


def main():
    ensure_app_dirs()
    app = Application()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
