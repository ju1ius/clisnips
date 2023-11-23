import time

import urwid

from clisnips.database import Snippet
from clisnips.tui.highlighters import highlight_command, highlight_documentation
from clisnips.tui.urwid_types import TextMarkup
from clisnips.tui.widgets.dialog import Dialog
from clisnips.tui.widgets.divider import HorizontalDivider


class ShowSnippetDialog(Dialog):
    def __init__(self, parent, snippet: Snippet):
        body = urwid.ListBox(
            urwid.SimpleListWalker(
                (
                    _field('Title:', ('snip:title', snippet['title'])),
                    HorizontalDivider(),
                    _field('Tags:', ('snip:tag', snippet['tag'])),
                    HorizontalDivider(),
                    _field('Command:', highlight_command(snippet['cmd'])),
                    HorizontalDivider(),
                    _field('Documentation:', highlight_documentation(snippet['doc'])),
                    HorizontalDivider(),
                    _info('Created on: ', _date(snippet['created_at'])),
                    _info('Last used on: ', _date(snippet['last_used_at'])),
                    _info('Usage count: ', snippet['usage_count']),
                    _info('Ranking: ', snippet['ranking']),
                ),
            ),
        )

        super().__init__(parent, body)


def _field(label: TextMarkup, content: TextMarkup):
    field = urwid.Pile(
        (
            urwid.Text(label),
            urwid.Text(content),
        ),
    )
    return field


def _info(label: str, value: str | float):
    return urwid.Text([label, ('info', str(value))])


def _date(timestamp: float) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(timestamp))
