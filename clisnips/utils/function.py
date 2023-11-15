from collections.abc import Callable
from typing import Any, Concatenate, Optional, TypeVar

T = TypeVar("T")


def bind(fn: Callable[Concatenate[T, ...], Any], obj: T, name: Optional[str] = None):
    """
    Turns `fn` into a bound method of `obj`, optionally renamed to `name`.
    """
    setattr(obj, name or fn.__name__, fn.__get__(obj))
