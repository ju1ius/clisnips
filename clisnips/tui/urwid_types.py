from typing import TypeVar


Text = TypeVar('Text', str, bytes)
AttributedText = Text | tuple[str, 'AttributedText[Text]']
UrwidMarkup = AttributedText[Text] | list[AttributedText[Text]]

TextMarkup = UrwidMarkup[str]
