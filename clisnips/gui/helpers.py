from gi.repository import GObject


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


class WidgetDecorator(GObject.GObject):

    def __init__(self, widget):
        GObject.GObject.__init__(self)
        self.widget = widget

    def __getattr__(self, name):
        return getattr(self.widget, name)
