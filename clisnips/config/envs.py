import os
from pathlib import Path

from clisnips.ty import AnyPath


def _db_path_from_env() -> AnyPath | None:
    match os.environ.get('CLISNIPS_DB'):
        case '' | None:
            return None
        case ':memory:':
            return ':memory:'
        case v:
            p = Path(v).expanduser().absolute()
            if p.is_file():
                return p
    return None


DB_PATH = _db_path_from_env()
