"""
parsing code adapted from:
https://bazaar.launchpad.net/~clicompanion-devs/clicompanion/trunk/view/head:/plugins/LocalCommandList.py
"""

import re
import time
from typing import Callable, TextIO

from clisnips.database.snippets_db import SnippetsDatabase
from clisnips.utils.list import pad_list

_ARGS_RE = re.compile(r'(?<!\\)((?:\\\\)*\?)')


def import_cli_companion(db: SnippetsDatabase, file: TextIO, log: Callable):
    start_time = time.time()
    log(('info', f'Importing snippets from {file.name}...'))

    db.insert_many(_get_snippets(file))
    log(('info', 'Rebuilding & optimizing search index...'))
    db.rebuild_index()
    db.optimize_index()

    elapsed_time = time.time() - start_time
    log(('success', f'Success: imported in {elapsed_time:.1f} seconds.'))


def _get_snippets(file):
    for row in _parse(file):
        yield _translate(row)


def _parse(file):
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


def _translate(row):
    """
    Since ui is free form text, we have to make an educated guess...
    """
    cmd, ui, desc = row
    now = time.time()
    result = {
        'title': desc,
        'cmd': cmd,
        'doc': ui,
        'tag': cmd.split(None, 1)[0],
        'created_at': now,
        'last_used_at': now,
        'usage_count': 0
    }
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
            doc.append('{%s} (string) %s' % (i, arg))
        result['doc'] = '\n'.join(doc)
        return result
    # try to find a space separated list
    by_space = [i.strip() for i in ui.split()]
    if len(by_space) == nargs:
        doc = []
        for i, arg in enumerate(by_space):
            doc.append('{%s} (string) %s' % (i, arg))
        result['doc'] = '\n'.join(doc)
        return result
    # else let ui be free form doc
    doc = [ui + '\n']
    for i in range(nargs):
        doc.append('{%s} (string)' % i)
    result['doc'] = '\n'.join(doc)
    return result
