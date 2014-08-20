import gtk


class BaseDialog(gtk.MessageDialog):

    def __init__(self,
                 flags=gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                 buttons=gtk.BUTTONS_OK,
                 **kwargs):
        super(BaseDialog, self).__init__(flags=flags,
                                         buttons=buttons,
                                         **kwargs)
        self.set_border_width(12)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

    def run(self, primary, secondary=''):
        self.set_markup(primary)
        self.format_secondary_markup(secondary)
        return super(BaseDialog, self).run()


class InfoDialog(BaseDialog):

    def __init__(self):
        super(InfoDialog, self).__init__(type=gtk.MESSAGE_INFO)


class WarningDialog(BaseDialog):

    def __init__(self):
        super(WarningDialog, self).__init__(type=gtk.MESSAGE_WARNING)


class QuestionDialog(BaseDialog):

    def __init__(self):
        super(QuestionDialog, self).__init__(type=gtk.MESSAGE_WARNING,
                                             buttons=gtk.BUTTONS_YES_NO)


def dialog(klass, primary, secondary='', **kwargs):
    dlg = klass(**kwargs)
    response = dlg.run(primary, secondary)
    dlg.destroy()
    return response


def info(primary, secondary='', **kwargs):
    return dialog(InfoDialog, primary, secondary, **kwargs)


def warning(primary, secondary='', **kwargs):
    return dialog(WarningDialog, primary, secondary, **kwargs)


def question(primary, secondary='', **kwargs):
    return dialog(QuestionDialog, primary, secondary, **kwargs)
