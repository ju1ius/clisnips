from typing import Any, Callable, Dict

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
        self._on_build_handlers: Dict[str, BuildCallback] = {}

    def register_screen(self, name: str, on_build: BuildCallback):
        self._on_build_handlers[name] = on_build

    def build_screen(self, name: str, display: bool = False, **kwargs) -> Screen:
        handler = self._on_build_handlers[name]
        screen = handler(**kwargs)
        if display:
            self.root_widget.original_widget = screen.view
        return screen
