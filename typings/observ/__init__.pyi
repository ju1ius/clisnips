from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Generic, TypeVar, TypedDict

T = TypeVar('T')

class Proxy(Generic[T]): ...

def proxy(target: T, readonly=False, shallow=False) -> T: ...
def to_raw(target: Proxy[T] | T) -> T: ...
def ref(target: T) -> Ref[T]: ...

class Ref(TypedDict, Generic[T]):
    value: T

Watchable = Callable[[], T] | T
WatchCallback = Callable[[], Any] | Callable[[T], Any] | Callable[[T, T], Any]

def watch(
    fn: Watchable[T],
    callback: WatchCallback[T] | None = None,
    sync: bool = False,
    deep: bool | None = None,
    immediate: bool = False,
) -> Watcher[T]: ...

class Watcher(Generic[T]): ...

reactive = proxy
readonly = partial(proxy, readonly=True)
shallow_reactive = partial(proxy, shallow=True)
shallow_readonly = partial(proxy, shallow=True, readonly=True)
