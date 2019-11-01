from typing import Iterable, Tuple, Union

_AttributedText = Union[str, Tuple[str, str]]
TextMarkup = Union[_AttributedText, Iterable[_AttributedText]]
