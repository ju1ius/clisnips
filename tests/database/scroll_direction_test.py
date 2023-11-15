from clisnips.database import ScrollDirection


def test_reverse():
    for orig, rev in (
        (ScrollDirection.FWD, ScrollDirection.BWD),
        (ScrollDirection.BWD, ScrollDirection.FWD),
    ):
        assert orig.reversed() is rev, 'Failed to reverse scroll direction'
