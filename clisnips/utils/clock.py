import time
from abc import ABC, abstractmethod


class Clock(ABC):
    @abstractmethod
    def now(self) -> float: ...


class MockClock(Clock):
    def __init__(self, now: float) -> None:
        self._now = now
        super().__init__()

    def now(self) -> float:
        return self._now


class SystemClock(Clock):
    def now(self) -> float:
        return time.time()
