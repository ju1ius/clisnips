from xml.dom.minidom import Document


class Exporter(object):

    name = 'clisnips'

    def __init__(self, db):
        self.db = db

    def export(self, filepath):
        self.export_rows(self.db, filepath)

    def export_rows(self, rows, filepath):
        doc = Document()
        root = doc.createElement('snippets')
        for row in rows:
            snip = self._create_snippet(doc, row)
            root.appendChild(snip)
        doc.appendChild(root)
        with open(filepath, 'w') as fp:
            xml = doc.toprettyxml(encoding='utf-8', indent='    ')
            fp.write(xml)

    def _create_snippet(self, doc, row):
        snip = doc.createElement('snippet')
        snip.setAttribute('created-at', row['created_at'])
        snip.setAttribute('last-used-at', row['last_used_at'])
        snip.setAttribute('usage-count', row['usage_count'])
        self.add_field(doc, snip, 'title', row['title'])
        self.add_field(doc, snip, 'command', row['cmd'])
        self.add_field(doc, snip, 'tag', row['tag'])
        self.add_field(doc, snip, 'doc', row['doc'])
        return snip

    def add_field(self, doc, parent, name, text):
        el = doc.createElement(name)
        txt = doc.createTextNode(text)
        el.appendChild(txt)
        parent.appendChild(el)
