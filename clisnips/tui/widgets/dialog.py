import enum
from typing import Optional

import urwid


class ResponseType(enum.Enum):
    NONE = 0
    ACCEPT = 1
    REJECT = 2


class DialogFrame(urwid.WidgetWrap):

    def __init__(self, parent, body, title=None):
        self.parent = parent
        self.line_box = urwid.LineBox(body, title=title)
        super().__init__(self.line_box)


class DialogOverlay(urwid.Overlay):

    def __init__(self, parent: urwid.Widget, *args, **kwargs):
        self.parent = parent
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key in ('esc', 'q'):
            self.parent.close_dialog()
        else:
            return super().keypress(size, key)


class Dialog(urwid.WidgetWrap):

    class Signals(enum.Enum):
        RESPONSE = 'response'

    def __init__(self, parent, body):
        self._parent = parent
        self._body = body
        self._frame = urwid.Frame(self._body, focus_part='body')
        w = self._frame
        # pad area around listbox
        w = urwid.Padding(w, ('fixed left', 2), ('fixed right', 2))
        w = urwid.Filler(w, ('fixed top', 1), ('fixed bottom', 1))
        w = urwid.AttrWrap(w, 'body')
        # "shadow" effect
        # w = urwid.Columns([w, ('fixed', 2, urwid.AttrWrap(urwid.Filler(urwid.Text(('border', '  ')), "top"), 'shadow'))])
        # w = urwid.Frame(w, footer=urwid.AttrWrap(urwid.Text(('border', '  ')), 'shadow'))
        # outermost border area
        # w = urwid.Padding(w, 'center', width)
        # w = urwid.Filler(w, 'middle', height)
        # w = urwid.AttrWrap(w, 'border')

        self.view = w

        super().__init__(w)

    def set_buttons(self, settings):
        buttons = []
        for label, response_type in settings:
            button = urwid.Button(label)
            urwid.connect_signal(button, 'click', self._on_button_clicked, user_args=response_type)
            button = urwid.AttrWrap(button, 'selectable', 'focus')
            buttons.append(button)
        action_area = urwid.GridFlow(buttons, 10, 3, 1, 'center')
        self._frame.footer = urwid.Pile([urwid.Divider(), action_area], focus_item=1)

    def _on_button_clicked(self, button, response_type):
        self._emit(self.Signals.RESPONSE, response_type)
