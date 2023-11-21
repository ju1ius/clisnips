import os
from pathlib import Path

from clisnips.ty import AnyPath

_APP = 'clisnips'


def xdg_config_home() -> Path:
    match os.environ.get('XDG_CONFIG_HOME'):
        case None | '':
            return Path('~/.config').expanduser()
        case v:
            return Path(v)


def xdg_data_home() -> Path:
    match os.environ.get('XDG_DATA_HOME'):
        case None | '':
            return Path('~/.local/share').expanduser()
        case v:
            return Path(v)


def xdg_state_home() -> Path:
    match os.environ.get('XDG_STATE_HOME'):
        case None | '':
            return Path('~/.local/state').expanduser()
        case v:
            return Path(v)


def xdg_runtime_dir() -> Path:
    match os.environ.get('XDG_RUNTIME_DIR'):
        case None | '':
            return xdg_state_home()
        case v:
            return Path(v)


def get_config_path(sub: AnyPath) -> Path:
    return xdg_config_home() / _APP / sub


def get_data_path(sub: AnyPath) -> Path:
    return xdg_data_home() / _APP / sub


def get_state_path(sub: AnyPath) -> Path:
    return xdg_state_home() / _APP / sub


def get_runtime_path(sub: AnyPath) -> Path:
    return xdg_runtime_dir() / _APP / sub


def ensure_app_dirs():
    for d in (
        get_config_path(''),
        get_data_path(''),
        get_state_path(''),
        get_runtime_path(''),
    ):
        d.mkdir(parents=True, exist_ok=True)
