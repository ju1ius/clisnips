import asyncio
from asyncio import Handle, TimerHandle
from collections.abc import Callable

__loop = asyncio.get_event_loop()


def get_event_loop():
    return __loop


def set_timeout(timeout: int | float, callback: Callable, *args) -> TimerHandle:
    return __loop.call_later(timeout / 1000, callback, *args)


def clear_timeout(handle: TimerHandle):
    handle.cancel()


def idle_add(callback: Callable, *args) -> Handle:
    return __loop.call_soon_threadsafe(callback, *args)
