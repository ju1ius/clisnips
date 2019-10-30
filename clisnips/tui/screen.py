from typing import Optional, List

import urwid


class Screen:
    """
    Base class for TUI screens
    """

    def __init__(self, signals: Optional[List[str]] = None):
        self.focused_widget: Optional[urwid.Widget] = None
        self.view: urwid.Widget = urwid.WidgetPlaceholder(urwid.SolidFill(' '))
        if signals:
            urwid.register_signal(self.__class__, signals)

    def quit(self, *args, **kwargs):
        raise urwid.ExitMainLoop()
