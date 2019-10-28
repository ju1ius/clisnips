from typing import Any


def pad_list(lst: list, pad_value: Any, pad_len: int) -> list:
    return lst + [pad_value] * (pad_len - len(lst))
