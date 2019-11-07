from pathlib import Path

import urwid

from clisnips.tui.logging import logger
from ..progress.message_queue import MessageType
from ..progress.worker import Worker
from ..dialog import Dialog, ResponseType
from ..divider import HorizontalDivider
from ..field import PathField
from ..spinner import Spinner


class ExportSnippetsDialog(Dialog):

    def __init__(self, parent, exporter):
        self._exporter = exporter
        self._path_field = PathField('Export path')
        self._progress_field = urwid.Pile([
            urwid.Text('')
        ])

        body = urwid.ListBox(urwid.SimpleListWalker([
            self._path_field,
            HorizontalDivider(),
            self._progress_field,
        ]))

        super().__init__(parent, body)
        self.set_buttons([
            ('Cancel', ResponseType.REJECT),
            ('Apply', ResponseType.ACCEPT),
        ])
        urwid.connect_signal(self, self.Signals.RESPONSE, self._on_response)

    def _on_response(self, dialog, response_type):
        if response_type == ResponseType.REJECT:
            self._parent.close_dialog()
        elif response_type == ResponseType.ACCEPT:
            self._export()

    def _get_export_path(self):
        path = self._path_field.get_value()
        path = Path(path).expanduser().absolute()
        directory: Path = path.parent
        directory.mkdir(parents=True, exist_ok=True)
        return path

    def _export(self):
        spinner = Spinner()
        status = urwid.Text('')
        progress_bar = urwid.ProgressBar('foo', 'bar')
        self._progress_field.contents[:] = [
            # (spinner, ('pack',)),
            (progress_bar, ('pack', None)),
            (status, ('pack', None)),
        ]
        path = self._get_export_path()

        worker = Worker.from_job(self._exporter, (path,))
        worker.listener.connect(MessageType.MESSAGE, lambda msg: status.set_text(msg))
        worker.listener.connect(MessageType.ERROR, lambda msg: status.set_text(msg))
        worker.listener.connect(MessageType.PROGRESS, lambda p: progress_bar.set_completion(p * 100))

        def on_finished():
            spinner.stop()
            self._parent.close_dialog()
        worker.listener.connect(MessageType.FINISHED, on_finished)

        spinner.start()
        worker.start()
