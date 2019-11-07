import sqlite3
import time
from typing import Callable, TextIO
from xml.dom.minidom import Document, Element

from ..database.snippets_db import SnippetsDatabase


def export(db: SnippetsDatabase, file: TextIO, log: Callable):
    start_time = time.time()
    num_rows = len(db)
    msg = f'{{progress:.0%}} Converting {num_rows:n} snippets to XML...'

    doc = Document()
    root = doc.createElement('snippets')
    for n, row in enumerate(db):
        snip = _create_snippet(doc, row)
        root.appendChild(snip)
        progress = msg.format(progress=n / num_rows)
        log(('info', progress), end='\r')
    doc.appendChild(root)

    log(('info', f'\nWriting {file.name} ...'))
    xml = doc.toprettyxml(indent='  ')
    file.write(xml)

    elapsed_time = time.time() - start_time
    log(('success', f'Success: exported {num_rows:n} snippets in {elapsed_time:.1f} seconds.'))


def _create_snippet(doc: Document, row: sqlite3.Row) -> Element:
    snip = doc.createElement('snippet')
    snip.setAttribute('created-at', str(row['created_at']))
    snip.setAttribute('last-used-at', str(row['last_used_at']))
    snip.setAttribute('usage-count', str(row['usage_count']))
    _add_field(doc, snip, 'title', row['title'])
    _add_field(doc, snip, 'command', row['cmd'])
    _add_field(doc, snip, 'tag', row['tag'])
    _add_field(doc, snip, 'doc', row['doc'], cdata=True)
    return snip


def _add_field(doc: Document, parent: Element, name: str, text: str, cdata: bool = False):
    el = doc.createElement(name)
    if cdata:
        txt = doc.createCDATASection(text)
    else:
        txt = doc.createTextNode(text)
    el.appendChild(txt)
    parent.appendChild(el)
