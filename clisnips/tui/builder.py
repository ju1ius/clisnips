from typing import Callable, Dict, Any

import urwid

from .screen import Screen


BuildCallback = Callable[[Any], Screen]


class Builder:
    """
    Screens builder

    Build UI screens and attaches their view to the top most widget.
    UI screens act like controllers for their child widgets and can interact
    directly with the main application instance.
    """

    def __init__(self, root_widget: urwid.WidgetPlaceholder):
        self.root_widget = root_widget
        self._build_callbacks: Dict[str, BuildCallback] = {}

    def register_screen(self, name: str, build_callback: BuildCallback):
        self._build_callbacks[name] = build_callback

    def build_screen(self, name: str, display: bool = False, **kwargs) -> Screen:
        build_callback = self._build_callbacks[name]
        screen = build_callback(**kwargs)
        if display:
            self.root_widget.original_widget = screen.view
        return screen
