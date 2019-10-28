import unittest

from clisnips.utils.common_prefix import common_prefix


class LongestCommonPrefixTest(unittest.TestCase):

    def testItWorksWithSortedSequence(self):
        choices = ['geek', 'geeks', 'geeze']
        self.assertEqual(common_prefix(*choices), 'gee')

    def testItWorksWithUnsortedSequence(self):
        choices = ['.gitignore', '.github', '.gitlab-ci.yml']
        self.assertEqual(common_prefix(*choices), '.git')

    def testItReturnsEmptyStringWhenNoCommonPrefix(self):
        choices = ['foo', 'bar', 'foobar', 'baz']
        self.assertEqual(common_prefix(*choices), '')
