from typing import TypeAlias, TypeVar


Text = TypeVar('Text', str, bytes)
AttributedText: TypeAlias = Text | tuple[str, 'AttributedText[Text]']
UrwidMarkup: TypeAlias = AttributedText[Text] | list[AttributedText[Text]]

TextMarkup: TypeAlias = UrwidMarkup[str]
