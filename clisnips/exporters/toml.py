from pathlib import Path
import time

import tomlkit

from .base import Exporter


class TomlExporter(Exporter):
    def export(self, path: Path):
        start_time = time.time()
        num_rows = len(self._db)
        self._log(('info', f'Converting {num_rows:n} snippets to TOML...'))

        document = tomlkit.document()
        items = tomlkit.aot()
        for row in self._db:
            tbl = tomlkit.table()
            tbl.update(row)
            if '\n' in row['cmd']:
                tbl['cmd'] = tomlkit.string(row['cmd'], multiline=True)
            if '\n' in row['doc']:
                tbl['doc'] = tomlkit.string(row['doc'], multiline=True)
            items.append(tbl)
        document.add('snippets', items)

        with open(path, 'w') as fp:
            fp.write(document.as_string())

        elapsed_time = time.time() - start_time
        self._log(('success', f'Success: exported {num_rows:n} snippets in {elapsed_time:.1f} seconds.'))
        return super().export(path)