import contextlib
import types

from urwid import signals


def original_widget(widget, recursive=False):
    while hasattr(widget, 'original_widget'):
        widget = widget.original_widget
        if not recursive:
            return widget
    return widget


@contextlib.contextmanager
def suspend_emitter(subject):
    emit = signals.emit_signal

    def suspended(self, obj, *rest):
        if subject is obj:
            return False
        return emit(self, obj, *rest)

    signals.emit_signal = types.MethodType(suspended, emit.__self__)
    try:
        yield
    finally:
        signals.emit_signal = emit


@contextlib.contextmanager
def suspend_signals():
    emit = signals.emit_signal
    signals.emit_signal = lambda *args: False
    try:
        yield
    finally:
        signals.emit_signal = emit
