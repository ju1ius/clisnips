from typing import TypeVar

T = TypeVar('T')


def pad_list(lst: list[T], pad_value: T, pad_len: int) -> list[T]:
    return lst + [pad_value] * (pad_len - len(lst))
