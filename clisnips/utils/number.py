from decimal import Decimal


def get_num_decimals(n) -> int:
    if isinstance(n, float):
        decimal_part = str(float(Decimal(n) % 1))
        return len(decimal_part.split('.')[1])
    return 0
