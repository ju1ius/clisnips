import gtk


class BuildableWidgetDecorator(object):

    def __init__(self, ui_file, name):
        self.ui = gtk.Builder()
        self.ui.add_from_file(ui_file)
        self.widget = self.ui.get_object(name)

    def add_ui_widget(self, name):
        setattr(self, name, self.ui.get_object(name))

    def add_ui_widgets(self, *names):
        for name in names:
            self.add_ui_widget(name)

    def connect_signals(self):
        self.ui.connect_signals(self)

    def __getattr__(self, name):
        return getattr(self.widget, name)


class WidgetDecorator(object):

    def __init__(self, widget):
        self.widget = widget

    def __getattr__(self, name):
        return getattr(self.widget, name)


class SimpleTextView(WidgetDecorator):

    def set_text(self, text):
        return self.widget.get_buffer().set_text(text)

    def get_text(self):
        buf = self.widget.get_buffer()
        start, end = buf.get_bounds()
        return buf.get_text(start, end)
