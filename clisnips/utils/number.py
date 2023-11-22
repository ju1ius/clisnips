from decimal import Decimal
import re
from typing import Any

# We rely on the fact that str(float(n)) will always normalize the number representation
FLOAT_RE = re.compile(
    r"""
    ^
        [-]? \d+
        (?:\. (?P<decimals> \d+ ))?
        (?:e- (?P<exponent> \d+ ))?
    $
    """,
    re.X,
)


def get_num_decimals(n: Any) -> int:
    try:
        n = float(n)
    except ValueError:
        return 0
    if n.is_integer():
        return 0
    d = 0
    match = FLOAT_RE.match(str(n))
    assert match
    if n := match['decimals']:
        d += len(n)
    if n := match['exponent']:
        d += int(n)
    return d


def is_integer_decimal(value: Decimal) -> bool:
    return value == value.to_integral_value()
