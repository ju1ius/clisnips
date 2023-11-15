from __future__ import annotations

from os import PathLike
from typing import Generic, Protocol, TypeVar, TypedDict, Union

AnyPath = Union[PathLike, str]

T = TypeVar('T')


class Ref(Generic[T], TypedDict):
  value: T


K = TypeVar('K', contravariant=True)
V = TypeVar('V', covariant=True)


class SupportsGetItem(Protocol, Generic[K, V]):
  def __getitem__(self: SupportsGetItem, key: K) -> V: ...
