from clisnips.database import SortOrder


def test_reverse():
    for orig, rev in (
        (SortOrder.ASC, SortOrder.DESC),
        (SortOrder.DESC, SortOrder.ASC),
    ):
        assert orig.reversed() is rev, 'Failed to reverse sort order'
