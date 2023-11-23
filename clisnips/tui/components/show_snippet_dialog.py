import time

import urwid

from clisnips.database import Snippet
from clisnips.tui.highlighters import highlight_command, highlight_documentation
from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.dialog import Dialog
from clisnips.tui.widgets.divider import HorizontalDivider


def _create_field(label: TextMarkup, content: TextMarkup):
    field = urwid.Pile(
        (
            urwid.Text(label),
            urwid.Text(content),
        ),
    )
    return field


class ShowSnippetDialog(Dialog):
    def __init__(self, parent, snippet: Snippet):
        body = urwid.ListBox(
            urwid.SimpleListWalker(
                (
                    _create_field('Title', snippet['title']),
                    HorizontalDivider(),
                    _create_field('Tags', snippet['tag']),
                    HorizontalDivider(),
                    _create_field('Command', highlight_command(snippet['cmd'])),
                    HorizontalDivider(),
                    _create_field('Documentation', highlight_documentation(snippet['doc'])),
                    HorizontalDivider(),
                    urwid.Text(f"Created on: {date(snippet['created_at'])}"),
                    urwid.Text(f"Last used on: {date(snippet['last_used_at'])}"),
                    urwid.Text(f"Usage count: {snippet['usage_count']}"),
                    urwid.Text(f"Ranking: {snippet['ranking']}"),
                ),
            ),
        )

        super().__init__(parent, body)


def date(timestamp: float):
    return time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))
