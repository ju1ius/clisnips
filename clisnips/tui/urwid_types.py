from collections.abc import Iterable

AttributedText = str | tuple[str, str]
TextMarkup = AttributedText | Iterable[AttributedText]
