import urwid


class HorizontalDivider(urwid.Divider):
    def __init__(self, margin_top: int = 0, margin_bottom: int = 0):
        super().__init__('─', top=margin_top, bottom=margin_bottom)
