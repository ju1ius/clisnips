
from clisnips.tui.layouts.table import LayoutColumn, LayoutRow, TableLayout


def render_cell(col: LayoutColumn, value: str) -> str:
    ps = ' ' * col.padding.start
    pe = ' ' * col.padding.end
    cell = value.ljust(col.computed_width - len(col.padding))
    return f'{ps}{cell}{pe}'


def render_row(row: LayoutRow) -> str:
    cells = []
    for col, data in row:
        cells.append(render_cell(col, str(data)))
    inner = '|'.join(cells)
    return f'|{inner}|'


def test_layout():
    table: TableLayout[dict[str, str]] = TableLayout()
    padding = (1, 1)
    table.append_column(LayoutColumn('a', padding=padding))
    table.append_column(LayoutColumn('b', padding=padding))
    table.append_column(LayoutColumn('c', padding=padding))

    rows = [
        {'a': 'one', 'b': 'two', 'c': 'three'},
        {'a': 'four', 'b': 'five', 'c': 'six'},
    ]
    expected = '''
| one  | two  | three |
| four | five | six   |
'''
    table.layout(rows, 0)
    result = []
    for row in table:
        result.append(render_row(row))
    result = '\n'.join(result)
    assert result == expected.strip()
