from xml.dom.minidom import Document


class Exporter(object):

    name = 'clisnips'

    def __init__(self, db):
        self.db = db

    def export(self, filepath):
        doc = Document()
        root = doc.createElement('snippets')
        for row in self.db:
            snip = doc.createElement('snippet')
            self.add_field(doc, snip, 'title', row['title'])
            self.add_field(doc, snip, 'command', row['cmd'])
            self.add_field(doc, snip, 'tag', row['tag'])
            self.add_field(doc, snip, 'doc', row['doc'])
            root.appendChild(snip)
        doc.appendChild(root)
        with open(filepath, 'w') as fp:
            xml = doc.toprettyxml(encoding='utf-8', indent='    ')
            fp.write(xml)

    def add_field(self, doc, parent, name, text):
        el = doc.createElement(name)
        txt = doc.createTextNode(text)
        el.appendChild(txt)
        parent.appendChild(el)
