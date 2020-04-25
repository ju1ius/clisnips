import urwid

from .widgets.dialog import DialogFrame, DialogOverlay
from .widgets.dialogs.error import ErrorDialog


class View(urwid.WidgetWrap):

    def __init__(self, view):
        self.view = view
        self._has_dialog = False
        self.placeholder = urwid.WidgetPlaceholder(urwid.Filler(urwid.Text('')))
        super().__init__(self.placeholder)
        self.placeholder.original_widget = urwid.AttrMap(self.view, 'view:default')

    def open_dialog(self, dialog, title: str = '', width=('relative', 80), height=('relative', 80)):
        frame = DialogFrame(self, dialog, title=title)
        overlay = DialogOverlay(self, frame, self.view, align='center', width=width, valign='middle', height=height)
        self._w.original_widget = overlay
        self._has_dialog = True

    def close_dialog(self):
        self._w.original_widget = self.view
        self._has_dialog = False

    def show_exception_dialog(self, err: Exception):
        dialog = ErrorDialog(self, err)
        self.open_dialog(dialog, 'Error')
