import logging
import time
from pathlib import Path
from xml.dom.minidom import Document, Element

from clisnips.database import Snippet
from clisnips.exporters.base import Exporter

logger = logging.getLogger(__name__)


class XmlExporter(Exporter):
    def export(self, path: Path):
        start_time = time.time()
        num_rows = len(self._db)
        logger.info(f'Converting {num_rows:n} snippets to XML')

        doc = Document()
        root = doc.createElement('snippets')
        for row in self._db:
            snip = _create_snippet(doc, row)
            root.appendChild(snip)
        doc.appendChild(root)
        xml = doc.toprettyxml(indent='  ')

        logger.debug(f'Writing snippets to {path} ...')
        with open(path, 'w') as fp:
            fp.write(xml)

        elapsed_time = time.time() - start_time
        logger.info(f'Exported {num_rows:n} snippets in {elapsed_time:.1f} seconds.', extra={'color': 'success'})


def _create_snippet(doc: Document, row: Snippet) -> Element:
    snip = doc.createElement('snippet')
    snip.setAttribute('created-at', str(row['created_at']))
    snip.setAttribute('last-used-at', str(row['last_used_at']))
    snip.setAttribute('usage-count', str(row['usage_count']))
    snip.setAttribute('ranking', str(row['ranking']))
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
