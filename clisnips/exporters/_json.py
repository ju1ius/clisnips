import json
import time
from typing import Callable, TextIO

from clisnips.database.snippets_db import SnippetsDatabase


def export(db: SnippetsDatabase, file: TextIO, log: Callable):
    start_time = time.time()
    num_rows = len(db)
    log(('info', f'Converting {num_rows:n} snippets to JSON...'))

    json.dump([dict(row) for row in db], file, indent=2)

    elapsed_time = time.time() - start_time
    log(('success', f'Success: exported {num_rows:n} snippets in {elapsed_time:.1f} seconds.'))
