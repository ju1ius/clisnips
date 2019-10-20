from gi.repository import GObject, Gtk, Pango

from ..utils import parse_color, parse_font


# ========== Fonts & Colors helpers


def set_font(widget, font):
    desc = parse_font(font)
    widget.modify_font(desc)


def set_background_color(widget, color, state=Gtk.StateFlags.NORMAL):
    color = parse_color(color)
    widget.modify_base(state, color)
    widget.modify_bg(state, color)


def set_text_color(widget, color, state=Gtk.StateFlags.NORMAL):
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
        props = {p.name: parent.child_get_property(old, p.name) for p in parent.list_child_properties()}
        parent.remove(old)
        parent.add(new)
        for name, value in props.items():
            parent.child_set_property(new, name, value)
    if old.get_property('visible'):
        new.show()
    else:
        new.hide()
    return new


class BuildableWidgetDecorator(GObject.GObject):

    WIDGET_IDS = ()
    UI_FILE = None
    MAIN_WIDGET = None

    def __init__(self):
        GObject.GObject.__init__(self)
        self.ui = Gtk.Builder()
        self.ui.add_from_file(str(self.UI_FILE))
        self.widget = self.ui.get_object(self.MAIN_WIDGET)
        self.widget.set_name(self.MAIN_WIDGET)
        if self.WIDGET_IDS:
            self.add_ui_widgets(*self.WIDGET_IDS)

    def add_ui_widget(self, name):
        widget = self.ui.get_object(name)
        if not widget:
            raise RuntimeError(f'No widget found with name "{name}"')
        widget.get_style_context().add_class(name)
        setattr(self, name, widget)

    def add_ui_widgets(self, *names):
        for name in names:
            self.add_ui_widget(name)

    def connect_signals(self):
        self.ui.connect_signals(self)

    def __getattr__(self, name):
        return getattr(self.widget, name)


class WidgetDecorator(GObject.GObject):

    def __init__(self, widget):
        GObject.GObject.__init__(self)
        self.widget = widget

    def __getattr__(self, name):
        return getattr(self.widget, name)


class SimpleTextView(WidgetDecorator):

    WINDOWS = {
        'widget': Gtk.TextWindowType.WIDGET,
        'text': Gtk.TextWindowType.TEXT,
        'left': Gtk.TextWindowType.LEFT,
        'right': Gtk.TextWindowType.RIGHT,
        'top': Gtk.TextWindowType.TOP,
        'bottom': Gtk.TextWindowType.BOTTOM
    }

    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_LAST, None, ())
    }

    def __init__(self, widget):
        super().__init__(widget)
        self._tab_width = 4
        self.set_tab_width(self._tab_width, force=True)
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
        if not isinstance(start, Gtk.TextIter):
            start = self.buffer.get_iter_at_offset(start)
        if not isinstance(end, Gtk.TextIter):
            end = self.buffer.get_iter_at_offset(end)
        if isinstance(tag, Gtk.TextTag):
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
        return buf.get_text(start, end, False)

    def set_font(self, spec):
        set_font(self.widget, spec)
        self.set_tab_width(self._tab_width, force=True)

    def set_tab_width(self, width, force=False):
        if width < 1:
            return
        if not force and width == self._tab_width:
            return
        tab_size = self._calculate_tab_size(width, ' ')
        if not tab_size:
            return
        tab_array = Pango.TabArray(1, True)
        tab_array.set_tab(0, Pango.TabAlign.LEFT, tab_size)
        self.widget.set_tabs(tab_array)
        self._tab_width = width

    def get_tab_width(self):
        return self._tab_width

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
            context = self.widget.get_style_context()
            color = context.get_background_color(Gtk.StateFlags.NORMAL)
        for win in ('left', 'right', 'top', 'bottom'):
            win = self.widget.get_window(self.WINDOWS[win])
            if win:
                set_background_color(win, color)

    def _calculate_tab_size(self, tab_width, tab_char):
        tab_str = tab_char * tab_width
        layout = self.widget.create_pango_layout(tab_str)
        if not layout:
            return
        width, height = layout.get_pixel_size()
        return width
