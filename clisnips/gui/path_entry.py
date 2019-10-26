"""
A port of the Thunar PathEntry widget.
https://github.com/xfce-mirror/thunar/blob/master/thunar/thunar-path-entry.c
"""

import locale
import os
from os import PathLike
from pathlib import Path
from typing import Optional, Tuple, Union

from gi.repository import GLib, Gdk, Gio, Gtk

from ..utils.common_prefix import common_prefix


def _was_modifier_pressed(modifier: Gdk.ModifierType, event_state: Optional[Gdk.ModifierType] = None) -> bool:
    """
    https://developer.gnome.org/gtk3/stable/gtk-migrating-checklist.html
    """
    default_modifiers = Gtk.accelerator_get_default_mod_mask()
    if event_state is None:
        has_event, event_state = Gtk.get_current_event_state()
        if not has_event:
            return False
    return (event_state & default_modifiers) == modifier


def _was_control_pressed(event_state: Optional[Gdk.ModifierType] = None) -> bool:
    return _was_modifier_pressed(Gdk.ModifierType.CONTROL_MASK, event_state)


class _File:

    def __init__(self, file: Union[PathLike, Gio.File]):
        if isinstance(file, Gio.File):
            self._file = file
        else:
            self._file = Gio.File.new_for_path(str(file))

    def __getattr__(self, attr):
        return getattr(self._file, attr)

    def __eq__(self, other):
        return isinstance(other, _File) and self._file.get_path() == other.get_path()

    def __str__(self):
        return self._file.get_path()


class _Folder(_File):
    pass


class _Model(Gtk.ListStore):

    COLUMN_ICON, COLUMN_FILENAME, COLUMN_FILEPATH, COLUMN_IS_DIR = range(4)
    COLUMNS = (Gio.Icon, str, str, bool)

    def __init__(self):
        super().__init__(*self.COLUMNS)

    def get_icon(self, it: Gtk.TreeIter):
        return self.get(it, self.COLUMN_ICON)[0]

    def get_filename(self, it: Gtk.TreeIter):
        return self.get(it, self.COLUMN_FILENAME)[0]

    def get_filepath(self, it: Gtk.TreeIter):
        return self.get(it, self.COLUMN_FILEPATH)[0]


class _EntryCompletion(Gtk.EntryCompletion):

    def __init__(self):
        Gtk.EntryCompletion.__init__(self)
        self.set_popup_single_match(False)
        self.set_model(_Model())
        pixbuf_cell = Gtk.CellRendererPixbuf()
        self.pack_start(pixbuf_cell, expand=False)
        self.add_attribute(pixbuf_cell, 'gicon', _Model.COLUMN_ICON)
        text_cell = Gtk.CellRendererText()
        self.pack_start(text_cell, expand=False)
        self.add_attribute(text_cell, 'text', _Model.COLUMN_FILENAME)

    def do_insert_prefix(self, *args, **kwargs):
        print('Gtk.EntryCompletion.do_insert_prefix')


class PathEntry(Gtk.Entry):

    def __init__(self, working_directory: Optional[PathLike] = None):
        super().__init__()
        self._cwd: Path = Path.cwd()
        if working_directory:
            self.set_working_directory(working_directory)
        #
        self._current_folder = None
        self._has_completion = False
        self._in_change = False
        self._check_completion_idle_id = 0
        #
        completion: _EntryCompletion = _EntryCompletion()
        completion.set_match_func(self._completion_match_callback)
        completion.connect('match-selected', self._on_completion_match_selected)
        #
        # need to connect the "key-press-event" before the GtkEntry class connects the completion signals,
        # so we get the Tab key before its handled as part of the completion stuff.
        self.connect('key-press-event', self._on_key_press)
        #
        self.set_completion(completion)
        # we connect to signals because overriding vfuncs is broken
        # see https://gitlab.gnome.org/GNOME/pygobject/issues/367
        self.connect('focus', self._do_focus)
        self.connect('activate', self._do_activate)
        self.connect('insert-text', self._do_insert_text)
        self.connect('changed', self._do_changed)
        # clear the auto completion whenever the cursor is moved manually or the selection is changed manually
        self.connect('notify::cursor-position', self._on_clear_completion)
        self.connect('notify::selection-bound', self._on_clear_completion)

    def get_working_directory(self) -> Path:
        return self._cwd

    def set_working_directory(self, directory: PathLike):
        self._cwd = Path(directory).expanduser().resolve(True)

    # thunar_path_entry_focus
    def _do_focus(self, entry, direction: Gtk.DirectionType):
        if direction == Gtk.DirectionType.TAB_FORWARD and self.has_focus() and not _was_control_pressed():
            if not self._has_completion and self._is_cursor_at_end():
                self._append_common_prefix(highlight=False)
            self._move_cursor_at_end()
            return True
        return super().do_focus(direction)

    # thunar_path_entry_key_press_event
    def _on_key_press(self, entry: Gtk.Entry, event: Gdk.EventKey):
        if event.keyval == Gdk.KEY_Tab and not _was_control_pressed(event.state):
            if not self._has_completion and self._is_cursor_at_end():
                self._append_common_prefix(highlight=False)
            self._move_cursor_at_end()
            # emit "changed", so the completion window is popped up
            self.emit('changed')
            # we handled the event
            return True
        return False

    # thunar_path_entry_activate
    def _do_activate(self, *args, **kwargs):
        if self._has_completion:
            self._move_cursor_at_end()

    # thunar_path_entry_do_insert_text
    def _do_insert_text(self, entry, text, length, position):
        # self.get_buffer().insert_text(position, text, length)
        if not self._in_change:
            self._queue_check_completion()
        # return length + position

    # thunar_path_entry_changed
    def _do_changed(self, entry):
        if self._in_change:
            return
        text = self.get_text()
        dirname, basename = os.path.split(text)
        folder = self._resolve_directory(dirname)
        file_path = self._resolve_filepath(folder, basename)

        current_folder = folder or None
        # TODO: what for ?
        current_file = file_path or None
        # print(current_folder.get_path(), self._current_folder.get_path())

        if current_folder != self._current_folder:
            self._current_folder = current_folder
            self._populate_model(current_folder)

    # thunar_path_entry_clear_completion
    def _on_clear_completion(self, entry, bound):
        # reset the completion and apply the new text
        if self._has_completion:
            self._has_completion = False
            self._do_changed()

    # thunar_path_entry_match_func
    def _completion_match_callback(self, completion: _EntryCompletion, key: str, it: Gtk.TreeIter, user_data=None):
        model: _Model = completion.get_model()
        if not model:
            # model can be None while it is being populated
            return False
        text = self.get_text()
        if text.endswith(os.sep):
            return True
        filename = model.get_filename(it)
        return filename.startswith(os.path.basename(text))

    # thunar_path_entry_match_selected
    def _on_completion_match_selected(self, completion: _EntryCompletion, model: _Model, it: Gtk.TreeIter, data=None):
        name, is_dir = model.get(it, _Model.COLUMN_FILENAME, _Model.COLUMN_IS_DIR)
        if is_dir:
            # append a slash if we have a folder here
            name += os.sep
        text = self.get_text()
        # determine the offset of the last slash on the entry text
        last_slash_offset = text.rfind(os.sep) + 1
        # delete the previous text at the specified offset
        self.delete_text(last_slash_offset, -1)
        # insert the new file/folder name
        self.insert_text(name, last_slash_offset)
        # move the cursor to the end of the text entry
        self.set_position(-1)
        return True

    # thunar_path_entry_common_prefix_append
    def _append_common_prefix(self, highlight: bool = False):
        prefix, is_dir = self._find_common_prefix()
        if not prefix:
            return
        if is_dir:
            prefix += os.sep
        text = self.get_text()
        # determine the offset of the last slash on the entry text
        last_slash_offset = text.rfind(os.sep) + 1
        text_length = len(text) - last_slash_offset
        prefix_length = len(prefix)
        # append only if the prefix is longer than the already entered text
        if prefix_length > text_length:
            self._in_change = True
            self.delete_text(last_slash_offset, -1)
            self.insert_text(prefix, last_slash_offset)
            self._in_change = False
            # highlight the prefix if requested
            if highlight:
                self.select_region(last_slash_offset + text_length, last_slash_offset + prefix_length)
                self._has_completion = True

    # thunar_path_entry_common_prefix_lookup
    def _find_common_prefix(self) -> Union[Tuple[str, bool], Tuple[None, None]]:
        text = self.get_text()
        if text.endswith(os.sep):
            return None, None
        text = os.path.basename(text)
        model: _Model = self.get_completion().get_model()
        prefix, prefix_is_dir = '', False

        for icon, name, path, is_dir in model:
            if not name.startswith(text):
                continue
            if not prefix:
                prefix, prefix_is_dir = name, is_dir
            else:
                # since it's not a unique match we don't pass is_dir
                prefix, prefix_is_dir = common_prefix(prefix, name), False
        return prefix, prefix_is_dir

    # thunar_path_entry_queue_check_completion
    def _queue_check_completion(self):
        if self._check_completion_idle_id == 0:
            self._check_completion_idle_id = GLib.idle_add(self._check_completion_idle, priority=GLib.PRIORITY_HIGH)

    # thunar_path_entry_check_completion_idle
    def _check_completion_idle(self):
        text = self.get_text()
        if text and not text.endswith(os.sep):
            self._append_common_prefix(highlight=True)
        self._check_completion_idle_id = 0
        return False

    def _populate_model(self, directory: _Folder):
        completion = self.get_completion()
        attrs = ','.join((
            Gio.FILE_ATTRIBUTE_STANDARD_DISPLAY_NAME,
            Gio.FILE_ATTRIBUTE_STANDARD_FAST_CONTENT_TYPE,
            Gio.FILE_ATTRIBUTE_STANDARD_ICON,
        ))
        result = []
        for finfo in directory.enumerate_children(attrs, Gio.FileQueryInfoFlags.NONE):
            mime_type = finfo.get_attribute_as_string(Gio.FILE_ATTRIBUTE_STANDARD_FAST_CONTENT_TYPE)
            result.append((
                finfo.get_icon(),
                finfo.get_display_name(),
                os.path.join(directory.get_path(), finfo.get_display_name()),
                mime_type == 'inode/directory',
            ))
        result.sort(key=lambda x: locale.strxfrm(x[1]))
        result.sort(key=lambda x: x[3], reverse=True)

        model = completion.get_model()
        completion.set_model(None)
        model.clear()
        for icon, name, path, is_dir in result:
            model.append((icon, name, path, is_dir))
        completion.set_model(model)

    def _resolve_directory(self, path) -> _Folder:
        path = os.path.expanduser(path)
        if os.path.isabs(path):
            return _Folder(path)
        path = os.path.join(self._cwd, path)
        return _Folder(path)

    def _resolve_filepath(self, folder: _Folder, filename: str):
        if filename:
            return _File(folder.resolve_relative_path(filename))
        return folder

    def _is_cursor_at_end(self):
        return self.get_position() == self.get_text_length()

    def _move_cursor_at_end(self):
        self.set_position(self.get_text_length())
