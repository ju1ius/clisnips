import enum
from typing import Generic, TypeVar

import observ
import urwid
from urwid.command_map import Command

V = TypeVar('V')


class _State(enum.StrEnum):
    OFF = enum.auto()
    ON = enum.auto()


_LABELS = {_State.OFF: 'Off', _State.ON: 'On'}
_STATES = {_State.OFF: False, _State.ON: True}


class Switch(urwid.WidgetWrap, Generic[V]):
    class Signals(enum.StrEnum):
        CHANGED = enum.auto()

    signals = list(Signals)

    State = _State

    def __init__(
        self,
        state: _State = _State.OFF,
        caption: str = '',
        states: dict[_State, V] | None = None,
        labels: dict[_State, str] | None = None,
    ):
        self._icon = urwid.SelectableIcon('<=>', 1)
        self._states = states or _STATES
        self._values = {v: s for s, v in self._states.items()}

        labels = labels or _LABELS
        self._off_label = urwid.AttrMap(urwid.Text(labels[_State.OFF]), 'choice:inactive')
        self._on_label = urwid.AttrMap(urwid.Text(labels[_State.ON]), 'choice:inactive')

        inner = urwid.Columns(
            [
                ('pack', urwid.Text(('caption', caption))),
                ('pack', self._off_label),
                ('pack', urwid.AttrMap(self._icon, 'icon', 'icon:focused')),
                ('pack', self._on_label),
            ],
            dividechars=1,
            focus_column=2,
        )
        super().__init__(inner)
        self._state = observ.ref(state)
        self._watchers = {
            'state': observ.watch(lambda: self._state['value'], self._handle_state_changed, immediate=True)
        }

    def set_value(self, value: V):
        self.set_state(self._values[value], emit=False)

    def sizing(self):
        return frozenset((urwid.Sizing.FLOW,))

    def keypress(self, size: tuple[int], key: str) -> str | None:
        match self._command_map[key]:
            case Command.ACTIVATE:
                self.toggle_state(emit=True)
            case _:
                return key

    def set_state(self, new_state: _State, emit=False):
        self._state['value'] = new_state
        if emit:
            self._emit(self.Signals.CHANGED, self._states[new_state])

    def toggle_state(self, emit=False):
        match self._state['value']:
            case _State.OFF:
                self.set_state(_State.ON, emit)
            case _State.ON:
                self.set_state(_State.OFF, emit)

    def _handle_state_changed(self, new_state, old_state):
        match new_state:
            case _State.OFF:
                self._icon.set_text('<==')
                self._off_label.attr_map = {None: 'choice:active'}
                self._on_label.attr_map = {None: 'choice:inactive'}
            case _State.ON:
                self._icon.set_text('==>')
                self._off_label.attr_map = {None: 'choice:inactive'}
                self._on_label.attr_map = {None: 'choice:active'}
