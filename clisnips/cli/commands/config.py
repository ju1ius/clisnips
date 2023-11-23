import argparse
import json
import sys

from clisnips.config.settings import AppSettings

from ..command import Command


def configure(cmd: argparse.ArgumentParser):
    cmd.add_argument('--schema', action='store_true', help='Shows the JSON schema for the configuration.')

    return ConfigCommand


class ConfigCommand(Command):
    def run(self, argv) -> int:
        if argv.schema:
            schema = AppSettings.model_json_schema()
            json.dump(schema, sys.stdout, indent=2)
        else:
            self.container.config.write(sys.stdout)

        sys.stdout.write('\n')
        return 0
