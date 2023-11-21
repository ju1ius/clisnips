import time
from enum import StrEnum, auto
from typing import Self

from pydantic import Field
from typing_extensions import Annotated, TypedDict  # noqa: UP035 (pydantic needs this)


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


class ImportableSnippet(TypedDict):
    title: Annotated[str, Field(min_length=1)]
    cmd: Annotated[str, Field(min_length=1)]
    tag: Annotated[str, Field(default='')]
    doc: Annotated[str, Field(default='')]
    created_at: Annotated[int, Field(ge=0, default_factory=lambda: int(time.time()))]
    last_used_at: Annotated[int, Field(ge=0, default=0)]
    usage_count: Annotated[int, Field(ge=0, default=0)]
    ranking: Annotated[float, Field(ge=0.0, default=0.0)]
