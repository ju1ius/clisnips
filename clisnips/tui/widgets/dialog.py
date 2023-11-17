from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import urwid
from urwid.widget.constants import Align, VAlign, WHSettings

if TYPE_CHECKING:
    from clisnips.tui.view import View

from .divider import HorizontalDivider


class ResponseType(enum.Enum):
    NONE = 0
    ACCEPT = 1
    REJECT = 2


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

    @dataclass
    class Action:
        label: str
        response_type: ResponseType
        attr_map: str | Mapping[str, str] | None = None
        focus_attr_map: str | Mapping[str, str] | None = None

    def __init__(self, view: View, body: urwid.Widget):
        self._parent_view = view
        self._body = body
        self._action_area: Optional[urwid.GridFlow] = None
        self._frame = urwid.Pile([self._body])
        w = self._frame
        # pad area around listbox
        w = urwid.Padding(w, align=Align.LEFT, left=2, right=2, width=(WHSettings.RELATIVE, 100))
        w = urwid.Filler(w, valign=VAlign.TOP, top=1, bottom=1, height=(WHSettings.RELATIVE, 100))
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
        buttons = []
        cell_width = 0
        for action in actions:
            cell_width = max(cell_width, len(action.label))
            button = urwid.Button(action.label)
            urwid.connect_signal(button, 'click', self._on_button_clicked, user_args=(action,))
            if action.attr_map:
                button = urwid.AttrMap(button, action.attr_map, action.focus_attr_map or action.attr_map)
            buttons.append(button)
        cell_width += 4  # account for urwid internal button decorations
        self._action_area = urwid.GridFlow(buttons, cell_width=cell_width, h_sep=3, v_sep=1, align=Align.CENTER)
        footer = urwid.Pile([HorizontalDivider(), self._action_area], focus_item=1)
        self._frame.contents = [
            (self._body, ('weight', 1)),
            (footer, ('pack', None)),
        ]

    def _on_button_clicked(self, action: Action, button, *args):
        self._emit(self.Signals.RESPONSE, action.response_type, *args)
