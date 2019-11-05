import math
from typing import Optional, Tuple, Union


class Padding:

    def __init__(self, left: int = 0, right: int = 0):
        self.left = left
        self.right = right
        self.length = left + right

    def __len__(self):
        return self.length


class Column:
    """
    Represents a table column
    """

    def __init__(self, index: Union[str, int],
                 width: Optional[int] = None, min_width: int = 0, max_width: Union[int, float] = math.inf,
                 padding: Tuple[int, int] = (0, 0), wrap: bool = False):
        self.index = index
        self.width = width
        self.min_width = min_width
        self.max_width = max_width if max_width is math.inf else int(max_width)
        self.word_wrap = wrap
        self.padding = Padding(*padding)

        self.wrappable = True
        self.content_width = 0
        self.min_content_width = 0
        self.computed_width = 0

    @property
    def is_resizable(self) -> bool:
        return not self.is_fixed

    @property
    def is_fixed(self) -> bool:
        return self.width or not self.word_wrap or not self.wrappable

    @property
    def attr_map(self):
        return {None: f'table-column:{self.index}'}

    @property
    def focus_attr_map(self):
        return {
            f'table-column:{self.index}': f'table-column:{self.index}:focused',
        }

    def compute_width(self):
        self.computed_width = self.width or (self.content_width + self.padding.length)

    def compute_min_width(self):
        self.min_width = self.min_content_width + self.padding.length

    def __repr__(self):
        return f'<Column[{self.index}] ({self.computed_width})>'
