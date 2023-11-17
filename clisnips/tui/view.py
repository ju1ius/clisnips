from collections.abc import Callable, Hashable

import urwid

from .widgets.dialog import Dialog, DialogFrame, DialogOverlay
from .widgets.dialogs.error import ErrorDialog


class View(urwid.WidgetWrap):
    """
    View instances act like controllers for their child widgets,
    and can interact directly with the main application instance.
    """

    def __init__(self, view: urwid.Widget):
        self._view = view
        self._wrapped_widget = urwid.AttrMap(self._view, 'view:default')
        super().__init__(self._wrapped_widget)
        self._has_dialog = False

    def open_dialog(self, dialog: Dialog, title: str = '', width=('relative', 80), height=('relative', 80)):
        frame = DialogFrame(self, dialog, title=title)
        overlay = DialogOverlay(self, frame, self._view, align='center', width=width, valign='middle', height=height)
        self._wrapped_widget.original_widget = overlay
        self._has_dialog = True

    def close_dialog(self):
        self._wrapped_widget.original_widget = self._view
        self._has_dialog = False

    def show_exception_dialog(self, err: Exception):
        dialog = ErrorDialog(self, err)
        self.open_dialog(dialog, 'Error')


BuildCallback = Callable[..., View]


class ViewBuilder:
    """
    Builds UI Views and attaches them to the root application widget.
    """

    def __init__(self, root_widget: urwid.WidgetPlaceholder):
        self.root_widget = root_widget
        self._on_build_handlers: dict[Hashable, BuildCallback] = {}

    def register(self, view_id: Hashable, on_build: BuildCallback):
        self._on_build_handlers[view_id] = on_build

    def build(self, view_id: Hashable, display: bool = False, **kwargs) -> View:
        handler = self._on_build_handlers[view_id]
        view = handler(**kwargs)
        if display:
            self.root_widget.original_widget = view
        return view
