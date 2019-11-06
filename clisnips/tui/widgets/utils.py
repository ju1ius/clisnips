
def original_widget(widget, recursive=False):
    while hasattr(widget, 'original_widget'):
        widget = widget.original_widget
        if not recursive:
            return widget
    return widget

