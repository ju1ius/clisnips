from types import CodeType
from clisnips.syntax.documentation.executor import Executor
from clisnips.syntax.documentation.nodes import CodeBlock, Documentation


def _make_doc_stub(*blocks: str):
    return Documentation(
        header='',
        parameters={},
        code_blocks=[CodeBlock(c) for c in blocks],
    )


def test_compile_str():
    result = Executor.compile_str("print('Hello')")
    assert isinstance(result, CodeType)


def test_execute_single():
    code = """
import os.path
if fields['infile'] and not fields['outfile']:
    path, ext = os.path.splitext(fields['infile'])
    fields['outfile'] = path + '.mp4'
"""
    doc = _make_doc_stub(code)
    # execute code
    ctx = {
        'fields': {
            'infile': '/foo/bar.wav',
            'outfile': '',
        },
    }
    result = Executor(doc).execute(ctx)
    assert result['fields']['outfile'] == '/foo/bar.mp4'


def test_execute_multiple():
    doc = _make_doc_stub(
        r"""test['x'] = 42""",
        r"""test['x'] *= 2""",
        r"""test['x'] = f'19{test["x"]}'""",
        r"""by = 'Orwell'""",
    )
    result = Executor(doc).execute({'test': {}})
    assert result['test']['x'] == '1984'
    assert result['by'] == 'Orwell'
