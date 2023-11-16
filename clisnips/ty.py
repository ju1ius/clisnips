from __future__ import annotations

from os import PathLike
from typing import Generic, TypeVar, TypedDict

T = TypeVar('T')
AnyPath = PathLike | str


class Ref(Generic[T], TypedDict):
    value: T
