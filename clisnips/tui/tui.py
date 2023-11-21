import atexit
import signal
import sys
from collections.abc import Callable, Hashable, Iterable

import observ
import urwid

from .loop import get_event_loop
from .view import View, ViewBuilder


class TUI:
    def __init__(self, palette):
        self.root_widget = urwid.WidgetPlaceholder(urwid.SolidFill(''))
        self.builder = ViewBuilder(self.root_widget)
        # Since our main purpose is to insert stuff in the tty command line, we send the screen to STDERR
        # so we can capture stdout easily without swapping file descriptors
        screen = urwid.raw_display.Screen(output=sys.stderr)
        for name, entry in palette.items():
            if isinstance(entry, str):
                entry = palette[entry]
            screen.register_palette_entry(
                name, entry['fg'], entry['bg'], entry.get('mono'), entry.get('fg_hi'), entry.get('bg_hi')
            )
            # screen.register_palette_entry(name, entry.fg, entry.bg, entry.mono, entry.fg_hi, entry.bg_hi)

        observ.scheduler.register_asyncio()
        self.main_loop = urwid.MainLoop(
            self.root_widget,
            handle_mouse=False,
            pop_ups=True,
            screen=screen,
            event_loop=get_event_loop(),
            unhandled_input=self._on_unhandled_input,
        )

    def register_view(self, name: Hashable, build_callback: Callable):
        self.builder.register(name, build_callback)

    def build_view(self, name: Hashable, display: bool, **kwargs) -> View:
        view = self.builder.build(name, display, **kwargs)
        return view

    def refresh(self):
        if self.main_loop.screen.started:
            self.main_loop.draw_screen()

    @staticmethod
    def connect(obj: object, name: Hashable, callback: Callable, weak_args: Iterable = (), user_args: Iterable = ()):
        urwid.connect_signal(obj, name, callback, weak_args=weak_args, user_args=user_args)

    def main(self):
        signal.signal(signal.SIGINT, self._on_terminate_signal)
        signal.signal(signal.SIGQUIT, self._on_terminate_signal)
        signal.signal(signal.SIGTERM, self._on_terminate_signal)

        self.main_loop.run()

    def stop(self):
        raise urwid.ExitMainLoop()

    def exit_with_message(self, message: str):
        atexit.register(lambda: print(message, sep=''))
        self.main_loop.screen.clear()
        self.stop()

    def _on_unhandled_input(self, key) -> bool:
        if key in ('esc', 'q'):
            self.stop()
            return True
        return False

    @staticmethod
    def _on_terminate_signal(signum, frame):
        raise urwid.ExitMainLoop()
