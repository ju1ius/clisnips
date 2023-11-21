import enum
import functools
import os
import os.path
from collections.abc import Iterable
from dataclasses import dataclass
from locale import strxfrm
from pathlib import Path

__all__ = [
    'FileAttributes',
    'PathCompletionEntry',
    'PathCompletion',
    'PathCompletionProvider',
    'FileSystemPathCompletionProvider',
]

from clisnips.ty import AnyPath


class FileAttributes(enum.IntFlag):
    NONE = 0
    IS_FILE = 1
    IS_DIR = 2
    IS_LINK = 4
    IS_HIDDEN = 8


@functools.total_ordering
@dataclass
class PathCompletionEntry:
    display_name: str
    path: str
    attributes: FileAttributes
    is_dir: bool
    is_link: bool
    is_hidden: bool

    def __init__(self, name: str, path: str, attrs: FileAttributes) -> None:
        self.attributes = attrs
        self.is_dir = attrs & FileAttributes.IS_DIR == FileAttributes.IS_DIR
        self.is_hidden = attrs & FileAttributes.IS_HIDDEN == FileAttributes.IS_HIDDEN
        self.is_link = attrs & FileAttributes.IS_LINK == FileAttributes.IS_LINK
        self.display_name = f'{name}{os.sep}' if self.is_dir else name
        self.path = path

    def __lt__(self, other):
        if self.is_dir == other.is_dir:
            if self.is_hidden == other.is_hidden:
                return strxfrm(self.display_name) < strxfrm(other.display_name)
            return other.is_hidden < self.is_hidden
        return other.is_dir < self.is_dir


class PathCompletionProvider:
    def get_completions(self, path: AnyPath) -> Iterable[PathCompletionEntry]:
        raise NotImplementedError()


class PathCompletion:
    def __init__(self, provider: PathCompletionProvider, show_files=True, show_hidden=True):
        self._provider = provider
        self._show_files = show_files
        self._show_hidden = show_hidden

    def get_completions(self, path: AnyPath) -> list[PathCompletionEntry]:
        results = []
        match_part = self._get_match_part(path)
        for entry in self._provider.get_completions(path):
            if self._entry_matches(entry, match_part):
                results.append(entry)

        return sorted(results)

    @staticmethod
    def complete(path: AnyPath, completion: PathCompletionEntry) -> str:
        dir_part, file_part = os.path.split(path)
        return os.path.join(dir_part, completion.display_name)

    @staticmethod
    def _get_match_part(path: AnyPath) -> str:
        dir_part, file_part = os.path.split(path)
        return file_part

    def _entry_matches(self, entry: PathCompletionEntry, pattern: str) -> bool:
        if not self._show_files and not entry.is_dir:
            return False
        if not self._show_hidden and entry.is_hidden:
            return False
        if not entry.display_name.startswith(pattern):
            return False
        return True


class FileSystemPathCompletionProvider(PathCompletionProvider):
    def __init__(self, base_directory: AnyPath = '.'):
        self._base_dir = Path(base_directory).expanduser().resolve(strict=True)
        if not self._base_dir.is_dir():
            raise OSError(f'Not a directory: {self._base_dir}')

    def set_base_directory(self, path: AnyPath):
        self._base_dir = Path(path).expanduser().resolve(strict=True)

    def get_completions(self, path: AnyPath) -> Iterable[PathCompletionEntry]:
        directory = self._resolve_directory(path)
        yield from self._scan_directory(directory)

    def _resolve_directory(self, path: AnyPath) -> Path:
        dir_part, file_part = os.path.split(path)
        dir_part = os.path.expanduser(dir_part)
        if not os.path.isabs(dir_part):
            dir_part = self._base_dir / dir_part
        return Path(dir_part).expanduser().resolve(strict=True)

    def _scan_directory(self, path: Path):
        with os.scandir(path) as directory:
            # type entry os.DirEntry
            for entry in directory:
                attrs = self._get_entry_attributes(entry)
                yield PathCompletionEntry(entry.name, entry.path, attrs)

    @staticmethod
    def _get_entry_attributes(entry: os.DirEntry):
        attrs = FileAttributes.NONE
        if entry.is_dir():
            attrs |= FileAttributes.IS_DIR
        elif entry.is_file():
            attrs |= FileAttributes.IS_FILE
        if entry.is_symlink():
            attrs |= FileAttributes.IS_LINK
        if entry.name.startswith('.'):
            attrs |= FileAttributes.IS_HIDDEN
        return attrs
