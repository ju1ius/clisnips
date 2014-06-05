import string

import gtk


class FormatStringEditorDialog(gtk.Dialog):

    def __init__(self):
        self.formatter = string.Formatter()
        super(FormatStringEditorDialog, self).__init__(
            "String Formatter", None,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        )
        self.vbox.set_spacing(4)

        preview_vbox = gtk.VBox(False, 4)
        self.preview_label = gtk.Label()
        self.preview_label.set_alignment(0, 0.5)
        self.preview_entry = gtk.TextView()
        #self.preview_entry.set_sensitive(False)
        preview_vbox.pack_start(self.preview_label, False)
        preview_vbox.pack_start(self.preview_entry, False)

        self.fields_vbox = gtk.VBox(False, 4)

        self.vbox.pack_start(preview_vbox)
        #self.vbox.pack_start(gtk.HSeparator())
        self.vbox.pack_start(self.fields_vbox)

        self.show_all()

    def run(self, fmtstr):
        fields = [f for f in self.formatter.parse(fmtstr) if f[1] is not None]
        if not fields:
            return gtk.RESPONSE_ACCEPT
        self.format_string = fmtstr
        self.set_fields(fields)
        return super(FormatStringEditorDialog, self).run()

    def set_fields(self, fields):
        self.reset_fields()
        # counter for automatic field numbering
        auto_count = -1
        has_numeric_field = False
        for field in fields:
            literal_text, field_name, format_spec, conversion = field
            if field_name == '':
                if has_numeric_field:
                    raise ValueError("cannot mix manual and automatic field numbering")
                auto_count += 1
                field_name = auto_count
            else:
                try:
                    field_name = int(field_name)
                    is_numeric = True
                    has_numeric_field = True
                except ValueError:
                    is_numeric = False
                if is_numeric and auto_count > -1:
                    raise ValueError("cannot mix manual and automatic field numbering")
            self.add_field(field_name)
        self.fields_vbox.show_all()
        self.update_preview()

    def reset_fields(self):
        self.preview_label.set_text(self.format_string)
        #self.preview_entry.set_text('')
        self.preview_entry.get_buffer().set_text('')
        self.fields = []
        for child in self.fields_vbox.get_children():
            self.fields_vbox.remove(child)

    def add_field(self, field_name):
        vbox = gtk.VBox()
        label = gtk.Label(field_name)
        label.set_alignment(0, 0.5)
        entry = gtk.Entry()
        entry.connect('changed', self.on_field_change)

        vbox.pack_start(label, False)
        vbox.pack_start(entry, False)
        self.fields_vbox.pack_start(vbox)

        self.fields.append({
            'name': field_name,
            'entry': entry
        })

    def get_output(self):
        args, kwargs = [], {}
        for field in self.fields:
            key = field['name']
            value = field['entry'].get_text()
            if key:
                try:
                    key = int(key)
                    args.insert(key, value)
                except ValueError:
                    kwargs[key] = value
            else:
                args.append(value)
        return self.format_string.format(*args, **kwargs)

    def update_preview(self):
        self.preview_entry.get_buffer().set_text(self.get_output())

    def on_field_change(self, widget):
        self.update_preview()


if __name__ == "__main__":
    dlg = FormatStringEditorDialog()
    dlg.run('zip -r {infile} \\\n\t{outfile} "${{2}}"')
