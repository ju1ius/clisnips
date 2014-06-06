import gobject
import gtk
import pango


# ========== Fonts & Colors helpers


def parse_color(spec):
    if isinstance(spec, gtk.gdk.Color):
        return spec
    return gtk.gdk.color_parse(spec)


def parse_font(spec):
    if isinstance(spec, pango.FontDescription):
        return spec
    return pango.FontDescription(spec)


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

    def __init__(self, widget):
        super(SimpleTextView, self).__init__(widget)
        self._alignment = gtk.Alignment(0, 0, 1.0, 1.0)
        replace_widget(widget, self._alignment)
        self._alignment.add(widget)
        self._event_box = gtk.EventBox()
        replace_widget(self._alignment, self._event_box)
        self._event_box.add(self._alignment)

    def set_padding(self, padding):
        self._alignment.set_padding(padding, padding, padding, padding)

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
        set_background_color(self._event_box, spec)

    def set_text_color(self, spec):
        set_text_color(self.widget, spec)
