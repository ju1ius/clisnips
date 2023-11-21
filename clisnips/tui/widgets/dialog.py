from __future__ import annotations

import enum
from typing import TYPE_CHECKING

import urwid
from urwid.widget.constants import Align, VAlign, WHSettings

if TYPE_CHECKING:
    from clisnips.tui.view import View

from .divider import HorizontalDivider


class ResponseKind(enum.Enum):
    NONE = 0
    ACCEPT = 1
    REJECT = 2


class Action(urwid.WidgetWrap):
    class Signals(enum.StrEnum):
        ACTIVATED = enum.auto()

    signals = list(Signals)

    class Kind(enum.StrEnum):
        DEFAULT = enum.auto()
        SUGGESTED = enum.auto()
        DESTRUCTIVE = enum.auto()

    def __init__(self, label: str, response_kind: ResponseKind, kind: Kind = Kind.DEFAULT):
        self._response_kind = response_kind
        self._kind = kind
        self._enabled = True

        self._button = urwid.Button(label)
        self._attrs = urwid.AttrMap(self._button, self._get_attr_map())
        urwid.connect_signal(self._button, 'click', self._on_activated)

        super().__init__(self._attrs)

    def enable(self):
        self.toggle(True)

    def disable(self):
        self.toggle(False)

    def toggle(self, enabled: bool):
        self._enabled = enabled
        self._attrs.attr_map = self._get_attr_map()
        self._attrs.focus_map = self._get_attr_map()

    def _on_activated(self, btn):
        if self._enabled:
            self._emit(Action.Signals.ACTIVATED, self._response_kind)

    def _get_attr_map(self):
        if not self._enabled:
            return {None: 'action:disabled'}
        return {None: f'action:{self._kind}'}


class DialogFrame(urwid.WidgetWrap):
    def __init__(self, parent: urwid.Widget, body: Dialog, title: str):
        self.parent = parent
        self.line_box = urwid.LineBox(body, title=title)
        super().__init__(self.line_box)


class DialogOverlay(urwid.Overlay):
    def __init__(self, parent: urwid.Widget, *args, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)


class Dialog(urwid.WidgetWrap):
    class Signals(enum.StrEnum):
        RESPONSE = 'response'

    signals = list(Signals)

    Action = Action

    def __init__(self, view: View, body: urwid.Widget):
        self._parent_view = view
        self._body = body
        self._action_area = urwid.GridFlow((), 1, 3, 1, 'center')
        self._frame = urwid.Pile([self._body])
        w = self._frame
        # pad area around listbox
        w = urwid.Padding(w, align=Align.LEFT, left=2, right=2, width=(WHSettings.RELATIVE, 100))
        w = urwid.Filler(w, valign=VAlign.TOP, top=1, bottom=1, height=('relative', 100))
        w = urwid.AttrMap(w, 'body')
        super().__init__(w)

    def close(self):
        self._parent_view.close_dialog()

    def keypress(self, size, key):
        match key:
            case 'esc':
                self.close()
            case _:
                super().keypress(size, key)

    def set_actions(self, *actions: Action):
        cell_width = 0
        for action in actions:
            cell_width = max(cell_width, len(action._button.label))
            urwid.connect_signal(action, Action.Signals.ACTIVATED, self._on_action_activated)
        cell_width += 4  # account for urwid internal button decorations
        self._action_area = urwid.GridFlow(actions, cell_width=cell_width, h_sep=3, v_sep=1, align=Align.CENTER)
        footer = urwid.Pile([HorizontalDivider(), self._action_area], focus_item=1)
        self._frame.contents = [
            (self._body, ('weight', 1)),
            (footer, ('pack', None)),
        ]

    def _on_action_activated(self, action: Action, response_kind: ResponseKind):
        # TODO: pass the action to signal handler
        self._emit(self.Signals.RESPONSE, response_kind)
