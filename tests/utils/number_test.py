from clisnips.utils.number import get_num_decimals


def test_it_returns_zero_for_integers():
    result = get_num_decimals(42)
    assert result == 0


def test_it_returns_number_of_decimal_for_strings():
    result = get_num_decimals('0.25')
    assert result == 2

    result = get_num_decimals('-1.25e-3')
    assert result == 5


def test_it_returns_number_of_decimal_for_floats():
    result = get_num_decimals(0.25)
    assert result == 2

    result = get_num_decimals(1.255)
    assert result == 3

    result = get_num_decimals(0.0169)
    assert result == 4
