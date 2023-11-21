"""
Importer for CliCompanion2 local command lists.

The file format is a TSV list, where each line has 3 fields:
* the command, possibly including `?` argument placeholders.
* the «ui», a comma (or space) separated list of strings,
    which are the readable names of each `?` in the command
* a textual description of the command

Example:
```
mv ? ?<TAB>src, dest<TAB>Moves "src" to "dest"
```

The parsing code was adapted from:
https://bazaar.launchpad.net/~clicompanion-devs/clicompanion/trunk/view/head:/plugins/LocalCommandList.py
"""

import logging
import re
import time
from collections.abc import Iterable
from pathlib import Path
from typing import TextIO

from clisnips.database import ImportableSnippet
from clisnips.utils.list import pad_list

from .base import Importer, SnippetAdapter

logger = logging.getLogger(__name__)

# Looks for a question-mark that is not escaped
# (not preceded by an odd number of backslashes)
_ARGS_RE = re.compile(r'(?<!\\)((?:\\\\)*\?)')


class CliCompanionImporter(Importer):
    def import_path(self, path: Path) -> None:
        start_time = time.time()
        logger.info(f'Importing snippets from {path}')

        with open(path) as fp:
            if self._dry_run:
                for _ in _get_snippets(fp):
                    ...
            else:
                self._db.insert_many(_get_snippets(fp))
            logger.info('Rebuilding & optimizing search index')
            if not self._dry_run:
                self._db.rebuild_index()
                self._db.optimize_index()

        elapsed_time = time.time() - start_time
        logger.info(f'Imported in {elapsed_time:.1f} seconds.', extra={'color': 'success'})


def _get_snippets(file: TextIO) -> Iterable[ImportableSnippet]:
    for cmd, ui, desc in _parse(file):
        yield _translate(cmd, ui, desc)


def _parse(file: TextIO) -> list[tuple[str, str, str]]:
    commands, seen = [], set()
    # try to detect if the line is a old fashion config line
    # (separated by ':')
    no_tabs = True
    some_colon = False
    for line in file:
        line = line.strip()
        if not line:
            continue
        fields = [f.strip() for f in line.split('\t', 2)]
        cmd, ui, desc = pad_list(fields, '', 3)
        if ':' in cmd:
            some_colon = True
        if ui or desc:
            no_tabs = False
        row = (cmd, ui, desc)
        if cmd and row not in seen:
            seen.add(row)
            commands.append(row)
    if no_tabs and some_colon:
        # None of the commands had tabs,
        # and at least one had ':' in the cmd...
        # This is most probably an old config style.
        for i, (cmd, ui, desc) in enumerate(commands):
            fields = [f.strip() for f in cmd.split('\t', 2)]
            cmd, ui, desc = pad_list(fields, '', 3)
            commands[i] = (cmd, ui, desc)
    return commands


def _translate(cmd: str, ui: str, desc: str) -> ImportableSnippet:
    """
    Since ui is free form text, we have to make an educated guess...
    """
    result = SnippetAdapter.validate_python(
        {
            'title': desc,
            'cmd': cmd,
            'doc': ui,
            'tag': cmd.split(None, 1)[0],
        }
    )
    nargs = len(_ARGS_RE.findall(cmd))
    if not nargs:
        # no user arguments
        return result
    # replace ?s by numbered params
    for i in range(nargs):
        cmd = _ARGS_RE.sub('{%s}' % i, cmd, count=1)
    result['cmd'] = cmd
    # try to find a comma separated list
    by_comma = [i.strip() for i in ui.split(',')]
    if len(by_comma) == nargs:
        doc = []
        for i, arg in enumerate(by_comma):
            doc.append('{%s} (string) %s' % (i, arg))  # noqa: UP031
        result['doc'] = '\n'.join(doc)
        return result
    # try to find a space separated list
    by_space = [i.strip() for i in ui.split()]
    if len(by_space) == nargs:
        doc = []
        for i, arg in enumerate(by_space):
            doc.append('{%s} (string) %s' % (i, arg))  # noqa: UP031
        result['doc'] = '\n'.join(doc)
        return result
    # else let ui be free form doc
    doc = [ui + '\n']
    for i in range(nargs):
        doc.append('{%s} (string)' % i)
    result['doc'] = '\n'.join(doc)
    return result
