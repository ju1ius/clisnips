from enum import StrEnum, auto
from typing import Self, TypedDict


class ScrollDirection(StrEnum):
    FWD = auto()
    BWD = auto()

    def reversed(self) -> Self:
        match self:
            case ScrollDirection.FWD:
                return ScrollDirection.BWD
            case ScrollDirection.BWD:
                return ScrollDirection.FWD


class SortOrder(StrEnum):
    ASC = 'ASC'
    DESC = 'DESC'

    @classmethod
    def _missing_(cls, value: object) -> Self | None:
        match str(value).upper():
            case 'ASC':
                return SortOrder.ASC
            case 'DESC':
                return SortOrder.DESC
            case _:
                return None

    def reversed(self) -> Self:
        match self:
            case SortOrder.ASC:
                return SortOrder.DESC
            case SortOrder.DESC:
                return SortOrder.ASC


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


class Snippet(TypedDict):
    id: int
    title: str
    cmd: str
    tag: str
    doc: str
    created_at: int
    last_used_at: int
    usage_count: int
    ranking: float


class NewSnippet(TypedDict):
    title: str
    cmd: str
    tag: str
    doc: str
