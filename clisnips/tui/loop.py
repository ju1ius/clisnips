import asyncio
from asyncio import TimerHandle
from typing import Callable, Union

__loop = asyncio.get_event_loop()


def get_event_loop():
    return __loop


IdleHandle = int


def set_timeout(timeout: Union[int, float], callback: Callable, *args) -> TimerHandle:
    return __loop.call_later(timeout / 1000, callback, *args)


def clear_timeout(handle: TimerHandle):
    handle.cancel()


def idle_add(callback: Callable, *args):
    __loop.call_soon_threadsafe(callback, *args)
