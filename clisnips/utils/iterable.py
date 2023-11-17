from collections.abc import Iterable
from typing import TypeVar

T = TypeVar('T')
D = TypeVar('D')


def intersperse(delimiter: D, iterable: Iterable[T]) -> Iterable[T | D]:
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x
