import time
from typing import Protocol


class Clock(Protocol):
    def now(self) -> float:
        ...


class MockClock(Clock):
    def __init__(self, now: float = 0.0) -> None:
        self._now = now

    def now(self) -> float:
        return self._now


class SystemClock(Clock):
    def now(self) -> float:
        return time.time()
