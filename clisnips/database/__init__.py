from enum import StrEnum, auto


class ScrollDirection(StrEnum):
    FWD = auto()
    BWD = auto()

    def reverse(self):
        if self is ScrollDirection.FWD:
            return ScrollDirection.BWD
        return ScrollDirection.FWD


class SortOrder(StrEnum):
    ASC = 'ASC'
    DESC = 'DESC'

    @classmethod
    def _missing_(cls, value: object):
        value = str(value).upper()
        for member in cls:
            if member.value == value:
                return member
        return None

    def reverse(self):
        if self is SortOrder.ASC:
            return SortOrder.DESC
        return SortOrder.DESC


class Column(StrEnum):
    ID = 'rowid'
    TITLE = auto()
    CMD = auto()
    TAGS = auto()
    DOC = auto()
    RANKING = auto()
    USAGE_COUNT = auto()
    LAST_USED_AT = auto()
    CREATED_AT = auto()


class SortColumn(StrEnum):
    RANKING = str(Column.RANKING)
    USAGE_COUNT = str(Column.USAGE_COUNT)
    LAST_USED_AT = str(Column.LAST_USED_AT)
    CREATED_AT = str(Column.CREATED_AT)
