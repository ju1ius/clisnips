from abc import ABC, abstractmethod
from typing import Generic, Self, TypeVar

from .snippets_db import QueryParameters


Row = TypeVar('Row')
Page = list[Row]


class Pager(ABC, Generic[Row]):
    @property
    @abstractmethod
    def page_size(self) -> int:
        ...

    @property
    @abstractmethod
    def page_count(self) -> int:
        ...

    @property
    @abstractmethod
    def current_page(self) -> int:
        ...

    @property
    @abstractmethod
    def is_first_page(self) -> bool:
        ...

    @property
    @abstractmethod
    def is_last_page(self) -> bool:
        ...

    @property
    @abstractmethod
    def must_paginate(self) -> bool:
        ...

    @property
    @abstractmethod
    def total_rows(self) -> int:
        ...

    @abstractmethod
    def set_query(self, query: str, params: QueryParameters = ()):
        ...

    @abstractmethod
    def get_query(self) -> str:
        ...

    @abstractmethod
    def set_count_query(self, query: str, params: QueryParameters = ()):
        ...

    @abstractmethod
    def set_page_size(self, size: int):
        ...

    @abstractmethod
    def execute(self, params: QueryParameters = (), count_params: QueryParameters = ()) -> Self:
        ...

    @abstractmethod
    def get_page(self, page: int) -> Page[Row]:
        ...

    @abstractmethod
    def first(self) -> Page[Row]:
        ...

    @abstractmethod
    def last(self) -> Page[Row]:
        ...

    @abstractmethod
    def next(self) -> Page[Row]:
        ...

    @abstractmethod
    def previous(self) -> Page[Row]:
        ...

    def __len__(self) -> int:
        return self.page_count

    @abstractmethod
    def count(self):
        """
        Updates the pager internal count by re-querying the database.
        """
        ...
