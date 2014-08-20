import os
from traceback import format_exc

from ..config import styles
from .helpers import BuildableWidgetDecorator, SimpleTextView


__DIR__ = os.path.abspath(os.path.dirname(__file__))


class ErrorDialog(BuildableWidgetDecorator):

    UI_FILE = os.path.join(__DIR__, 'resources', 'error_dialog.ui')
    MAIN_WIDGET = 'error_dialog'
    WIDGET_IDS = ('message_lbl', 'details_textview', 'details_vbox')

    def __init__(self):
        super(ErrorDialog, self).__init__()
        self.widget.set_skip_taskbar_hint(True)
        self.widget.set_skip_pager_hint(True)

        self.details_textview = SimpleTextView(self.details_textview)
        self.details_textview.set_font(styles.font)
        self.details_textview.set_background_color(styles.bgcolor)
        self.details_textview.set_text_color(styles.fgcolor)
        self.details_textview.set_padding(4)

    def run(self, message, details=''):
        if isinstance(message, Exception):
            message = '{}{}: {}'.format(
                details + '\n' if details else '',
                message.__class__.__name__,
                str(message)
            )
            details = format_exc()
        self.details_vbox.set_visible(bool(details))
        self.message_lbl.set_text(message)
        self.details_textview.set_text(details)
        response = self.widget.run()
        self.widget.destroy()
        return response
