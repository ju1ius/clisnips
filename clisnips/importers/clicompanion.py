"""
parsing code adapted from:
http://bazaar.launchpad.net/~clicompanion-devs/clicompanion/trunk/view/head:/plugins/LocalCommandList.py 
"""

import re
import time

from .utils import pad_list


ARGS_RE = re.compile(r'(?<!\\)((?:\\\\)*\?)')


class Importer(object):

    name = 'clicompanion2'

    def __init__(self, db):
        self.db = db

    def import_file(self, filepath):
        try:
            self.db.insertmany(self.get_snippets(filepath))
        except Exception as err:
            raise err
        else:
            self.db.save()

    def get_snippets(self, filepath):
        for row in self.parse(filepath):
            yield self.translate(row)

    def parse(self, filepath):
        commands, seen = [], set()
        with open(filepath, 'r') as fp:
            # try to detect if the line is a old fashion config line
            # (separated by ':') 
            no_tabs = True
            some_colon = False
            for line in fp:
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

    def translate(self, row):
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
        nargs = len(ARGS_RE.findall(cmd))
        if not nargs:
            # no user arguments
            return result
        # replace ?s by numbered params
        for i in range(nargs):
            cmd = ARGS_RE.sub('{%s}' % i, cmd, count=1)
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
