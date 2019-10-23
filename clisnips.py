#!/usr/bin/env python3

import sys

from clisnips.gui.app import Application


if __name__ == '__main__':

    app = Application()
    app.run(sys.argv)

    sys.exit(0)
