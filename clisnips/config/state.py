from __future__ import annotations

import json
from typing import TypedDict

from clisnips.database import SortColumn, SortOrder
from .paths import get_state_path


class PersistentState(TypedDict):
    page_size: int
    sort_by: SortColumn
    sort_order: SortOrder


DEFAULTS: PersistentState = {
    'page_size': 25,
    'sort_by': SortColumn.RANKING,
    'sort_order': SortOrder.ASC,
}


def load_persistent_state() -> PersistentState:
    try:
        with open(get_state_path('state.json')) as fp:
            data = json.load(fp)
            return _merge_defaults(data)
    except FileNotFoundError:
        return DEFAULTS.copy()


def save_persistent_state(state: PersistentState):
    with open(get_state_path('state.json'), 'w') as fp:
        json.dump(state, fp, indent=2)


def _merge_defaults(data: dict) -> PersistentState:
    result = DEFAULTS.copy()
    if v := data.get('page_size'):
        result['page_size'] = int(v)
    if v := data.get('sort_by'):
        result['sort_by'] = SortColumn(v)
    if v := data.get('sort_order'):
        result['sort_order'] = SortOrder(v)
    return result
