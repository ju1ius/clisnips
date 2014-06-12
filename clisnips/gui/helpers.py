import gobject
import gtk

from ..utils import parse_font, parse_color


# ========== Fonts & Colors helpers


def set_font(widget, font):
    desc = parse_font(font)
    widget.modify_font(desc)


def set_background_color(widget, color, state=gtk.STATE_NORMAL):
    color = parse_color(color)
    widget.modify_base(state, color)
    widget.modify_bg(state, color)


def set_text_color(widget, color, state=gtk.STATE_NORMAL):
    color = parse_color(color)
    widget.modify_fg(state, color)
    widget.modify_text(state, color)


def set_cursor_color(widget, primary, secondary=None):
    primary = parse_color(primary)
    if secondary:
        secondary = parse_color(secondary)
    else:
        secondary = primary
    widget.modify_cursor(primary, secondary)


# ========== Widgets helpers


def replace_widget(old, new):
    parent = old.get_parent()
    if parent is not None:
        props = []
        for pspec in parent.list_child_properties():
            props.append(pspec.name)
            props.append(parent.child_get_property(old, pspec.name))
        parent.remove(old)
        parent.add_with_properties(new, *props)
    if old.flags() & gtk.VISIBLE:
        new.show()
    else:
        new.hide()


class BuildableWidgetDecorator(gobject.GObject):

    WIDGET_IDS = ()
    UI_FILE = None
    MAIN_WIDGET = None

    def __init__(self):
        gobject.GObject.__init__(self)
        self.ui = gtk.Builder()
        self.ui.add_from_file(self.UI_FILE)
        self.widget = self.ui.get_object(self.MAIN_WIDGET)
        if self.WIDGET_IDS:
            self.add_ui_widgets(*self.WIDGET_IDS)

    def add_ui_widget(self, name):
        setattr(self, name, self.ui.get_object(name))

    def add_ui_widgets(self, *names):
        for name in names:
            self.add_ui_widget(name)

    def connect_signals(self):
        self.ui.connect_signals(self)

    def __getattr__(self, name):
        return getattr(self.widget, name)


class WidgetDecorator(gobject.GObject):

    def __init__(self, widget):
        gobject.GObject.__init__(self)
        self.widget = widget

    def __getattr__(self, name):
        return getattr(self.widget, name)


class SimpleTextView(WidgetDecorator):

    WINDOWS = {
        'widget': gtk.TEXT_WINDOW_WIDGET,
        'text': gtk.TEXT_WINDOW_TEXT,
        'left': gtk.TEXT_WINDOW_LEFT,
        'right': gtk.TEXT_WINDOW_RIGHT,
        'top': gtk.TEXT_WINDOW_TOP,
        'bottom': gtk.TEXT_WINDOW_BOTTOM
    }

    __gsignals__ = {
        'changed': gobject.signal_query('changed', gtk.TextBuffer)[3:]
    }

    def __init__(self, widget):
        super(SimpleTextView, self).__init__(widget)
        self.buffer.connect('changed', self._on_buffer_changed)

    @property
    def buffer(self):
        return self.widget.get_buffer()

    def _on_buffer_changed(self, buf):
        self.emit('changed')

    def create_tag(self, name=None, **props):
        return self.buffer.create_tag(name, **props)

    def apply_tag(self, tag, start, end):
        # convert offsets to iter
        if not isinstance(start, gtk.TextIter):
            start = self.buffer.get_iter_at_offset(start)
        if not isinstance(end, gtk.TextIter):
            end = self.buffer.get_iter_at_offset(end)
        if isinstance(tag, gtk.TextTag):
            self.buffer.apply_tag(tag, start, end)
        else:
            self.buffer.apply_tag_by_name(str(tag), start, end)

    def remove_all_tags(self, start=None, end=None):
        if not start:
            start = self.buffer.get_start_iter()
        if not end:
            end = self.buffer.get_end_iter()
        self.buffer.remove_all_tags(start, end)

    def set_text(self, text):
        return self.widget.get_buffer().set_text(text)

    def get_text(self):
        buf = self.widget.get_buffer()
        start, end = buf.get_bounds()
        return buf.get_text(start, end)

    def set_font(self, spec):
        set_font(self.widget, spec)

    def set_background_color(self, spec):
        set_background_color(self.widget, spec)
        self._update_background(spec)

    def set_text_color(self, spec):
        set_text_color(self.widget, spec)

    def set_cursor_color(self, primary, secondary=None):
        set_cursor_color(self.widget, primary, secondary)

    def set_padding(self, padding):
        for win in ('left', 'right', 'top', 'bottom'):
            self.widget.set_border_window_size(self.WINDOWS[win], padding)
        self._update_background()

    def _update_background(self, color=None):
        if not color:
            style = self.widget.get_style()
            color = style.bg[gtk.STATE_NORMAL]
        for win in ('left', 'right', 'top', 'bottom'):
            win = self.widget.get_window(self.WINDOWS[win])
            if win:
                set_background_color(win, color)
