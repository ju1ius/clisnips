import enum
from typing import cast

import urwid
from urwid.command_map import Command
import observ

from clisnips.ty import Ref


class Switch(urwid.WidgetWrap):
    class Signals(enum.StrEnum):
        CHANGED = enum.auto()

    signals = list(Signals)

    class State(enum.StrEnum):
        OFF = enum.auto()
        ON = enum.auto()

    def __init__(self, state: State = State.OFF, caption: str = '', off_label: str = 'Off', on_label: str = 'On'):
        self._icon = urwid.SelectableIcon('<->', 1)
        self._off_label = urwid.Text(('label:off', off_label))
        self._on_label = urwid.Text(('label:on', on_label))
        # TODO: correctly handle packing
        inner = urwid.Columns(
            [
                urwid.Text(('caption', caption)),
                self._off_label,
                urwid.AttrMap(self._icon, 'icon', 'icon:focused'),
                self._on_label,
            ],
            dividechars=1,
            focus_column=2,
        )
        super().__init__(inner)
        self._state = cast(Ref[Switch.State], observ.ref(state))
        self._watchers = {
            'state': observ.watch(lambda: self._state['value'], self._handle_state_changed, immediate=True)
        }

    def sizing(self):
        return frozenset((urwid.Sizing.FLOW,))

    def keypress(self, size: tuple[int], key: str) -> str | None:
        match self._command_map[key]:
            case Command.ACTIVATE:
                self.toggle_state(emit=True)
            case _:
                return key

    def set_state(self, new_state: State, emit=False):
        self._state['value'] = new_state
        if emit:
            self._emit(self.Signals.CHANGED, new_state)

    def toggle_state(self, emit=False):
        match self._state['value']:
            case self.State.OFF:
                self.set_state(self.State.ON, emit)
            case self.State.ON:
                self.set_state(self.State.OFF, emit)

    def _handle_state_changed(self, new_state, old_state):
        match new_state:
            case self.State.OFF:
                self._icon.set_text('<--')
            case self.State.ON:
                self._icon.set_text('-->')
