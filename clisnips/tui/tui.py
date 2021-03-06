import atexit
import signal
import sys
from typing import Callable, Iterable, Optional

import urwid

from . import theme
from .builder import Builder
from .loop import get_event_loop
from .screen import Screen


class TUI:

    def __init__(self):
        self.root_widget = urwid.WidgetPlaceholder(urwid.SolidFill(''))
        self.builder: Builder = Builder(self.root_widget)
        # Since our main purpose is to insert stuff in the tty command line, we send the screen to STDERR
        # so we can capture stdout easily without swapping file descriptors
        screen = urwid.raw_display.Screen(output=sys.stderr)
        self.main_loop = urwid.MainLoop(
            self.root_widget,
            handle_mouse=False,
            pop_ups=True,
            palette=theme.palette,
            screen=screen,
            event_loop=urwid.AsyncioEventLoop(loop=get_event_loop()),
            unhandled_input=self._on_unhandled_input,
        )
        self.main_loop.screen.set_terminal_properties(colors=256)

    def register_screen(self, name: str, build_callback: Callable):
        self.builder.register_screen(name, build_callback)

    def build_screen(self, name: str, display: bool, **kwargs) -> Screen:
        screen = self.builder.build_screen(name, display, **kwargs)
        return screen

    def refresh(self):
        if self.main_loop.screen.started:
            self.main_loop.draw_screen()

    @staticmethod
    def connect(obj: object, name: str, callback: Callable,
                weak_args: Optional[Iterable] = None, user_args: Optional[Iterable] = None):
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

    def _on_unhandled_input(self, key):
        if key in ('esc', 'q'):
            self.stop()
            return

    @staticmethod
    def _on_terminate_signal(signum, frame):
        raise urwid.ExitMainLoop()
