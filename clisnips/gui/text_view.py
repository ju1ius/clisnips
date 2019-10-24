from gi.repository import GObject, Gtk, Pango

from .helpers import WidgetDecorator


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

    def _calculate_tab_size(self, tab_width, tab_char):
        tab_str = tab_char * tab_width
        layout = self.widget.create_pango_layout(tab_str)
        if not layout:
            return
        width, height = layout.get_pixel_size()
        return width
