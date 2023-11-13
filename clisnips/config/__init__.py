import json
from pathlib import Path

from clisnips._types import AnyPath
from .settings import AppSettings
from .envs import DB_PATH
from .paths import get_config_path, get_runtime_path
from .palette import Palette, default_palette

VERSION = "0.1"
AUTHORS = ['Jules Bernable (ju1ius)']
HELP_URI = 'https://github.com/ju1ius/clisnips/wiki'
LICENSE = """\
Copyright (C) {authors}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
""".format(authors=', '.join(AUTHORS))


def _parse_json() -> AppSettings:
    match get_config_path('settings.json'):
        case p if p.exists():
            with open(p) as fp:
                settings = AppSettings.model_validate_json(fp.read(), strict=True)
        case _:
            settings = AppSettings()
    return settings


class Config:

    def __init__(self):
        self._cfg = _parse_json()

    @property
    def database_path(self) -> AnyPath:
        if DB_PATH is not None:
            return DB_PATH
        path = self._cfg.database
        if path == ':memory:':
            return path
        return Path(path).expanduser().absolute()

    @property
    def palette(self):
        p = default_palette
        p.update(self._cfg.palette) # type: ignore
        return p
    
    @property
    def log_file(self):
        return get_runtime_path('logs.sock')

    def write(self, fp):
        data = {
            'database': str(self.database_path),
            'palette': self.palette,
        }
        json.dump(data, fp, indent=2)
