from os.path import abspath, dirname, join
from pathlib import Path

from gi.repository import GObject, Gtk, GtkSource

from .helpers import set_font
from ..config import styles
from ..utils import get_luminance

__DIR__ = Path(__file__).parent.absolute()


class Buffer(GtkSource.Buffer):

    def __init__(self):
        super().__init__()
        self.set_highlight_matching_brackets(True)
        self.set_highlight_syntax(True)


class SourceView(GtkSource.View):

    __gsignals__ = {
        'changed': GObject.signal_query('changed', Gtk.TextBuffer)[3:]
    }

    def __init__(self):
        super().__init__()
        self.set_show_line_numbers(True)
        self.set_insert_spaces_instead_of_tabs(True)
        self.set_tab_width(2)
        self.set_indent_on_tab(True)
        self.set_auto_indent(True)
        #
        buf = Buffer()
        buf.connect('changed', self._on_buffer_changed)
        self.set_buffer(buf)
        #
        self.set_theme()

    def set_text(self, text, undoable=True):
        buf = self.get_buffer()
        if not undoable:
            buf.begin_not_undoable_action()
        buf.set_text(text)
        if not undoable:
            buf.end_not_undoable_action()

    def get_text(self):
        buf = self.get_buffer()
        start, end = buf.get_bounds()
        return buf.get_text(start, end, False)

    def set_font(self, font):
        set_font(self, font)

    def set_syntax(self, syntax):
        lang = get_syntax(syntax)
        self.get_buffer().set_language(lang)

    def set_theme(self, scheme=None):
        scheme = get_theme(scheme) if scheme else get_default_theme()
        self.get_buffer().set_style_scheme(scheme)

    def _on_buffer_changed(self, buf):
        self.emit('changed')


class LanguageManager(GtkSource.LanguageManager):

    def __init__(self):
        super().__init__()
        path = self.get_search_path()
        path.append(str(__DIR__ / 'resources' / 'sourceview'))
        self.set_search_path(path)


class StyleManager(GtkSource.StyleSchemeManager):

    def __init__(self):
        super().__init__()
        self.append_search_path(str(__DIR__ / 'resources' / 'sourceview'))


__language_manager = None
__style_manager = None


def get_language_manager():
    global __language_manager
    if __language_manager is None:
        __language_manager = LanguageManager()
    return __language_manager


def get_syntax(lang):
    return get_language_manager().get_language(lang)


def get_doc_syntax(self):
    return get_syntax('clisnips-doc')


def get_cmd_syntax(self):
    return get_syntax('clisnips-cmd')


def get_style_manager():
    global __style_manager
    if __style_manager is None:
        __style_manager = StyleManager()
    return __style_manager 


def get_theme(scheme):
    return get_style_manager().get_scheme(scheme)


def get_default_theme():
    return get_theme('one-dark')
    # TODO: adaptive theme
    bgcolor = styles.bgcolor
    lum = get_luminance(bgcolor)
    if lum > 0.5:
        # light background
        return get_theme('solarizedlight')
    # dark background
    return get_theme('solarizeddark')
