import json
import time
from collections.abc import Callable
from typing import TextIO

from clisnips.database.snippets_db import SnippetsDatabase


def import_json(db: SnippetsDatabase, file: TextIO, log: Callable):
    start_time = time.time()
    log(('info', f'Importing snippets from {file.name}...'))

    db.insertmany(json.load(file))
    log(('info', 'Rebuilding & optimizing search index...'))
    db.rebuild_index()
    db.optimize_index()

    elapsed_time = time.time() - start_time
    log(('success', f'Success: imported in {elapsed_time:.1f} seconds.'))
