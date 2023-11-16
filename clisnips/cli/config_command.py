import argparse
import json
import sys

from clisnips.config.settings import AppSettings

from .command import Command


class ShowConfigCommand(Command):
    @classmethod
    def configure(cls, action: argparse._SubParsersAction):
        cmd = action.add_parser('config', help='Shows the current configuration.')
        cmd.add_argument('--schema', action='store_true', help='Shows the JSON schema for the configuration.')

    def run(self, argv) -> int:
        if argv.schema:
            schema = AppSettings.model_json_schema()
            json.dump(schema, sys.stdout, indent=2)
        else:
            self.container.config.write(sys.stdout)
        return 0
