from clisnips.utils.common_prefix import common_prefix


def test_it_works_with_sorted_sequence():
    choices = ['geek', 'geeks', 'geeze']
    assert common_prefix(*choices) == 'gee'


def test_it_works_with_unsorted_sequence():
    choices = ['.gitignore', '.github', '.gitlab-ci.yml']
    assert common_prefix(*choices) == '.git'


def test_it_returns_empty_string_when_no_common_prefix():
    choices = ['foo', 'bar', 'foobar', 'baz']
    assert common_prefix(*choices) == ''
