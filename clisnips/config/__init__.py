import json
from pathlib import Path

from clisnips.ty import AnyPath

from .envs import DB_PATH
from .paths import get_config_path, get_runtime_path
from .settings import AppSettings

SCHEMA_BASE_URI = 'https://raw.githubusercontent.com/ju1ius/clisnips/master/schemas'


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
        return self._cfg.palette.model_dump()

    @property
    def log_file(self):
        return get_runtime_path('logs.sock')

    def write(self, fp):
        data = {
            '$schema': f'{SCHEMA_BASE_URI}/settings.json',
            'database': str(self.database_path),
            'palette': self.palette,
        }
        json.dump(data, fp, indent=2)
