from typing import Iterable, TypeVar, Union

T = TypeVar('T')
D = TypeVar('D')


def join(delimiter: D, iterable: Iterable[T]) -> Iterable[Union[T, D]]:
    it = iter(iterable)
    yield next(it)
    for x in it:
        yield delimiter
        yield x
