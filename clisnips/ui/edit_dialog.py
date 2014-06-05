import os

import gtk
import pango

from .. import config
from . import helpers


__DIR__ = os.path.abspath(os.path.dirname(__file__))
UI_FILE = os.path.join(__DIR__, 'edit_dialog.ui')


class EditDialog(helpers.BuildableWidgetDecorator):

    def __init__(self):
        super(EditDialog, self).__init__(UI_FILE, 'edit_dialog')
        #self.ui.set_translation_domain (config.PKG_NAME)
        #self.widget.connect("destroy-event", self.on_destroy)
        #self.widget.set_icon_name("gnome-main-menu")

        self.add_ui_widgets(
            'desc_entry', 'cmd_textview', 'doc_textview', 'tags_entry'
        )
        monospace_font_desc = pango.FontDescription(config.font)
        self.cmd_textview.modify_font(monospace_font_desc)
        self.doc_textview.modify_font(monospace_font_desc)

        self.cmd_textview = helpers.SimpleTextView(self.cmd_textview)
        self.doc_textview = helpers.SimpleTextView(self.doc_textview)

        self.connect_signals()

    def run(self, data=None):
        self.reset_fields()
        if data:
            self.populate_fields(data)
        return self.widget.run()

    def populate_fields(self, data):
        self.item_id = data['id']
        self.desc_entry.set_text(data['title'])
        self.cmd_textview.set_text(data['cmd'])
        self.doc_textview.set_text(data['doc'])
        self.tags_entry.set_text(data['tag'])

    def reset_fields(self):
        self.item_id = None
        self.desc_entry.set_text('')
        self.cmd_textview.set_text('')
        self.doc_textview.set_text('')
        self.tags_entry.set_text('')

    def get_data(self):
        return {
            'id': self.item_id,
            'title': self.desc_entry.get_text(),
            'cmd': self.cmd_textview.get_text(),
            'doc': self.doc_textview.get_text(),
            'tag': self.tags_entry.get_text(),
        }

    ###########################################################################
    # ------------------------------ SIGNALS
    ###########################################################################

    def on_edit_dialog_response(self, widget, response_id):
        if response_id == gtk.RESPONSE_ACCEPT:
            self.widget.hide()
        elif response_id == gtk.RESPONSE_REJECT:
            self.reset_fields()
            self.widget.hide()
        elif response_id == gtk.RESPONSE_DELETE_EVENT:
            self.reset_fields()
            self.widget.hide()
            return True
        return False
