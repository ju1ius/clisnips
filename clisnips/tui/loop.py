import asyncio
import functools
from asyncio import Handle, TimerHandle
from collections.abc import Callable
from typing import Any

import urwid

__loop = asyncio.get_event_loop()
__uloop = urwid.AsyncioEventLoop(loop=__loop)


def get_event_loop():
    return __uloop


def set_timeout(timeout: int | float, callback: Callable, *args) -> TimerHandle:
    if not args:
        return __uloop.alarm(timeout / 1000, callback)
    return __uloop.alarm(timeout / 1000, lambda: callback(*args))


def clear_timeout(handle: TimerHandle):
    __uloop.remove_alarm(handle)


def idle_add(callback: Callable, *args) -> Handle:
    return __loop.call_soon_threadsafe(callback, *args)


def debounce(fn: Callable[..., Any], delay: int = 300):
    handle = None

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        nonlocal handle
        if handle:
            clear_timeout(handle)

        def handler():
            nonlocal handle
            handle = None
            fn(*args, **kwargs)

        handle = set_timeout(delay, handler)

    return wrapper


def debounced(delay: int = 300):
    return functools.partial(debounce, delay=delay)
