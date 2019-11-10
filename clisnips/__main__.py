import sys

from clisnips.cli import Application


def main():
    app = Application()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
