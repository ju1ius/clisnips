from contextlib import suppress

import urwid

from .field import Entry, SimpleField
from ..edit import EmacsEdit
from ..menu import PopupMenu
from ...urwid_types import TextMarkup
from ...._types import AnyPath
from ....utils.path_completion import FileSystemPathCompletionProvider, PathCompletion, PathCompletionEntry


class PathField(SimpleField):

    def __init__(self, label: TextMarkup, *args, **kwargs):
        entry = PathEntry(*args, **kwargs)
        super().__init__(label, entry)


class PathEntry(Entry, urwid.PopUpLauncher):

    signals = ['changed']

    def __init__(self, cwd: AnyPath = '.', mode: str = '', default: str = ''):
        self._completion = PathCompletion(FileSystemPathCompletionProvider(cwd))

        self._menu = PathCompletionMenu()
        urwid.connect_signal(self._menu, 'closed', lambda *x: self.close_pop_up())
        urwid.connect_signal(self._menu, 'completion-selected', self._on_completion_selected)

        self._entry = EmacsEdit('', default)
        self._entry.keypress = self._on_entry_key_pressed
        urwid.connect_signal(self._entry, 'postchange', lambda *x: self._emit('changed'))

        super().__init__(self._entry)

    def get_value(self):
        return self._entry.get_edit_text()

    def create_pop_up(self):
        return self._menu

    def get_pop_up_parameters(self):
        return {'left': 0, 'top': 1, 'overlay_width': 40, 'overlay_height': 20}

    def _trigger_completion(self):
        text = self._entry.get_edit_text()
        try:
            completions = self._completion.get_completions(text)
        except FileNotFoundError:
            return
        if not completions:
            return
        if len(completions) == 1:
            self._insert_completion(completions[0])
            return
        self._menu.set_completions(completions)
        self.open_pop_up()

    def _on_entry_key_pressed(self, size, key):
        if key == 'tab':
            self._trigger_completion()
            return
        return EmacsEdit.keypress(self._entry, size, key)

    def _on_completion_selected(self, menu, entry: PathCompletionEntry):
        self._insert_completion(entry)
        self.close_pop_up()

    def _insert_completion(self, entry: PathCompletionEntry):
        text = self._completion.complete(self._entry.get_edit_text(), entry)
        self._entry.set_edit_text(text)
        self._entry.set_edit_pos(len(text))


class PathCompletionMenu(PopupMenu):

    signals = PopupMenu.signals + ['completion-selected']

    def set_completions(self, completions):
        items = []
        for entry in completions:
            item = PathCompletionMenuItem(entry)
            urwid.connect_signal(item, 'click', self._on_item_clicked, user_args=[entry])
            items.append(item)
        self._walker[:] = items
        self._walker.set_focus(0)

    def _on_item_clicked(self, entry, button):
        self._emit('completion-selected', entry)


class PathCompletionMenuItem(urwid.Button):
    button_left = urwid.Text('')
    button_right = urwid.Text('')

    def __init__(self, entry):
        icon = '📂' if entry.is_dir else '📄'
        super().__init__(f'{icon} {entry.display_name}')
