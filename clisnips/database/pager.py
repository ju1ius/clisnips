from abc import ABC, abstractmethod

from .snippets_db import QueryParameters, ResultSet


class Pager(ABC):

    @property
    @abstractmethod
    def page_size(self) -> int: ...

    @property
    @abstractmethod
    def page_count(self) -> int: ...

    @property
    @abstractmethod
    def current_page(self) -> int: ...

    @property
    @abstractmethod
    def is_first_page(self) -> bool: ...

    @property
    @abstractmethod
    def is_last_page(self) -> bool: ...

    @property
    @abstractmethod
    def must_paginate(self) -> bool: ...

    @property
    @abstractmethod
    def total_rows(self) -> int: ...

    @abstractmethod
    def set_query(self, query: str, params: QueryParameters = ()): ...

    @abstractmethod
    def get_query(self) -> str: ...

    @abstractmethod
    def set_count_query(self, query: str, params: QueryParameters = ()): ...

    @abstractmethod
    def set_page_size(self, size: int): ...

    @abstractmethod
    def execute(self, params: QueryParameters = (), count_params: QueryParameters = ()) -> 'Pager': ...

    @abstractmethod
    def get_page(self, page: int) -> ResultSet: ...

    @abstractmethod
    def first(self) -> ResultSet: ...

    @abstractmethod
    def last(self) -> ResultSet: ...

    @abstractmethod
    def next(self) -> ResultSet: ...

    @abstractmethod
    def previous(self) -> ResultSet: ...

    def __len__(self) -> int:
        return self.page_count

    @abstractmethod
    def count(self):
        """
        Updates the pager internal count by re-querying the database.
        """
        ...
