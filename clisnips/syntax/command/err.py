from collections.abc import Iterator

from .nodes import Field


class CommandTemplateError(Exception):
    ...


class InterpolationError(CommandTemplateError):
    def __init__(self, msg: str, field: Field) -> None:
        self.field = field
        super().__init__(msg)


class InvalidContext(InterpolationError):
    ...


class InterpolationErrorGroup(ExceptionGroup[InterpolationError]):
    def __iter__(self) -> Iterator[InterpolationError]:
        for err in self.exceptions:
            if isinstance(err, InterpolationError):
                yield err
            elif isinstance(err, self.__class__):
                yield from err
