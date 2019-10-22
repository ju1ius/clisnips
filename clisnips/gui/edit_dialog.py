from pathlib import Path

from gi.repository import Gtk

from .error_dialog import ErrorDialog
from .helpers import BuildableWidgetDecorator, SimpleTextView, replace_widget
# validation
from ..exceptions import ParsingError
from ..strfmt import doc_parser, fmt_parser

HAS_GTKSOURCEVIEW = True
try:
    from .source_view import SourceView
except ImportError:
    HAS_GTKSOURCEVIEW = False


__DIR__ = Path(__file__).parent.absolute()


class EditDialog(BuildableWidgetDecorator):

    UI_FILE = __DIR__ / 'resources' / 'glade' / 'edit_dialog.glade'
    MAIN_WIDGET = 'edit_dialog'
    WIDGET_IDS = ('desc_entry', 'cmd_textview', 'doc_textview', 'tags_entry')

    def __init__(self):
        super().__init__()
        #self.ui.set_translation_domain(config.PKG_NAME)

        self._setup_textviews()
        self.connect_signals()

        self._editable = True
        self._item_id = None

    def run(self, data=None):
        self.reset_fields()
        if data:
            self.populate_fields(data)
        response = self.widget.run()
        if not self._editable:
            return Gtk.ResponseType.REJECT
        return response

    def set_editable(self, editable):
        self._editable = editable
        for field in self.WIDGET_IDS:
            getattr(self, field).set_editable(editable)

    def populate_fields(self, data):
        self._item_id = data['id']
        self.desc_entry.set_text(data['title'])
        self.cmd_textview.set_text(data['cmd'])
        self.doc_textview.set_text(data['doc'])
        self.tags_entry.set_text(data['tag'])

    def reset_fields(self):
        if self._editable:
            self.widget.set_title('Edit snippet')
        else:
            self.widget.set_title('Snippet properties')
        self._item_id = None
        for field in self.WIDGET_IDS:
            getattr(self, field).set_text('')

    def get_data(self):
        return {
            'id': self._item_id,
            'title': self.desc_entry.get_text(),
            'cmd': self.cmd_textview.get_text(),
            'doc': self.doc_textview.get_text(),
            'tag': self.tags_entry.get_text(),
        }

    def _validate(self):
        errors = []
        title = self.desc_entry.get_text().strip()
        if not title:
            errors.append('You must provide a description.')
        #
        cmd = self.cmd_textview.get_text().strip()
        if not cmd:
            errors.append('You must provide a command.')
        else:
            try:
                tokens = [t for t in fmt_parser.parse(cmd)]
            except ParsingError as err:
                errors.append(f'You have an error in your snippet syntax:\n{err!s}')
        #
        doc = self.doc_textview.get_text().strip()
        if doc:
            try:
                doc_parser.parse(doc)
            except ParsingError as err:
                errors.append(f'You have an error in your documentation syntax:\n{err!s}')
        #
        if errors:
            ErrorDialog().run('\n'.join(errors))
            return False
        return True

    def _setup_textviews(self):
        views = ('cmd_textview', 'doc_textview')
        if HAS_GTKSOURCEVIEW:
            for name in views:
                view = getattr(self, name)
                src_view = SourceView()
                replace_widget(view, src_view)
                setattr(self, name, src_view)
            self.cmd_textview.set_syntax('clisnips-cmd')
            self.doc_textview.set_syntax('clisnips-doc')
        else:
            for name in views:
                view = getattr(self, name)
                view = SimpleTextView(view)
                setattr(self, name, view)

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def on_edit_dialog_response(self, widget, response_id):
        if not self._editable:
            self.widget.hide()
            return False
        if response_id == Gtk.ResponseType.ACCEPT:
            if not self._validate():
                self.widget.stop_emission('response')
                return False
            self.widget.hide()
        elif response_id == Gtk.ResponseType.REJECT:
            self.reset_fields()
            self.widget.hide()
        elif response_id == Gtk.ResponseType.DELETE_EVENT:
            self.reset_fields()
            self.widget.hide()
            return True
        return False
