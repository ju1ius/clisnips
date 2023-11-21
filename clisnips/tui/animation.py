import time
from collections.abc import Callable

from .loop import clear_timeout, set_timeout


class AnimationController:
    def __init__(self, callback: Callable, frame_rate: int = 60):
        self._callback = callback
        self._frame_duration = 1000 / frame_rate
        self._timeout_handle = None
        self._last_update = 0.0

    def toggle(self):
        self.stop() if self._timeout_handle else self.start()

    def start(self, *args):
        self._last_update = time.time() * 1000

        def loop(*cb_args):
            now = time.time() * 1000
            delta = (now - self._last_update) / self._frame_duration
            self._callback(delta, *cb_args)
            self._last_update = now
            self._timeout_handle = set_timeout(self._frame_duration, loop, *cb_args)

        self._timeout_handle = set_timeout(self._frame_duration, loop, *args)

    def stop(self):
        if self._timeout_handle:
            clear_timeout(self._timeout_handle)
            self._timeout_handle = None
