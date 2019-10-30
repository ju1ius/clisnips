import urwid


def original_widget(widget):
    if isinstance(widget, urwid.AttrMap):
        return widget.original_widget
    return widget

