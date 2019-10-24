import unittest

from clisnips.utils.number import get_num_decimals


class GetNumDecimalsTest(unittest.TestCase):

    def testItReturnsZeroForIntegers(self):
        result = get_num_decimals(42)
        self.assertEqual(result, 0)

    def testItReturnsNumberOfDecimalForStrings(self):
        result = get_num_decimals('0.25')
        self.assertEqual(result, 2)

        result = get_num_decimals('-1.25e-3')
        self.assertEqual(result, 5)

    def testItReturnsNumberOfDecimalForFloats(self):
        result = get_num_decimals(0.25)
        self.assertEqual(result, 2)

        result = get_num_decimals(1.255)
        self.assertEqual(result, 3)

        result = get_num_decimals(0.0169)
        self.assertEqual(result, 4)
