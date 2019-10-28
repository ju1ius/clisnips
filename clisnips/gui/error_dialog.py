from pathlib import Path
from textwrap import wrap
from traceback import format_exc

from gi.repository import Gtk

from .buildable import Buildable
from .text_view import SimpleTextView

__DIR__ = Path(__file__).parent.absolute()


@Buildable.from_file(__DIR__ / 'resources' / 'glade' / 'error_dialog.glade')
class ErrorDialog:

    dialog: Gtk.Dialog = Buildable.Child('error_dialog')
    details_textview: SimpleTextView = Buildable.Child()
    details_vbox: Gtk.Box = Buildable.Child()
    message_lbl: Gtk.Label = Buildable.Child()

    def __init__(self, transient_for=None):
        self.dialog.set_transient_for(transient_for)
        self.dialog.set_skip_taskbar_hint(True)
        self.dialog.set_skip_pager_hint(True)
        self.details_textview = SimpleTextView(self.details_textview)

    def run(self, message, details=''):
        if isinstance(message, Exception):
            message = '{}{}: {}'.format(
                details + '\n' if details else '',
                message.__class__.__name__,
                str(message)
            )
            details = format_exc()
        self.details_vbox.set_visible(bool(details))
        self.message_lbl.set_text('\n'.join(wrap(message)))
        self.details_textview.set_text(details)
        response = self.dialog.run()
        self.dialog.destroy()
        return response
