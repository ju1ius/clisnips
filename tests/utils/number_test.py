from decimal import Decimal
import pytest
from clisnips.utils.number import clamp_to_range, get_default_range_step, get_num_decimals, is_integer_decimal


@pytest.mark.parametrize(
    ('value', 'expected'),
    (
        (42, 0),
        (0.25, 2),
        (1.255, 3),
        (0.0169, 4),
        ('0.25', 2),
        ('1.25e-3', 5),
        (Decimal('0.25'), 2),
        (Decimal('1.25e-3'), 5),
    ),
)
def test_num_decimals(value, expected: int):
    result = get_num_decimals(value)
    assert result == expected


@pytest.mark.parametrize(
    ('value', 'expected'),
    (
        (Decimal('42'), True),
        (Decimal('42.0'), True),
        (Decimal('0.25'), False),
        (Decimal('1.25e-3'), False),
        (Decimal('1e-17'), False),
        (Decimal('1.333e3'), True),
    ),
)
def test_is_integer_decimal(value: Decimal, expected: bool):
    result = is_integer_decimal(value)
    assert result == expected


@pytest.mark.parametrize(
    ('start', 'end', 'expected'),
    (
        ('1', '10', '1'),
        ('0', '1.00', '1'),
        ('0.1', '10', '0.1'),
        ('0.1', '0.333', '0.001'),
        #
        ('-1', '-10', '1'),
    ),
)
def test_default_range_step(start, end, expected):
    result = get_default_range_step(Decimal(start), Decimal(end))
    assert result == Decimal(expected)


@pytest.mark.parametrize(
    ('value', 'start', 'end', 'expected'),
    (
        ('5', '1', '10', '5'),
        ('0', '1', '10', '1'),
        ('50', '1', '10', '10'),
        #
        ('-5', '-1', '-10', '-5'),
        ('0', '-1', '-10', '-1'),
        ('-50', '-1', '-10', '-10'),
    ),
)
def test_clamp_to_range(value, start, end, expected):
    result = clamp_to_range(Decimal(value), Decimal(start), Decimal(end))
    assert result == Decimal(expected)
