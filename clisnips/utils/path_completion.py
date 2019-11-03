import functools
import os.path
from dataclasses import dataclass
from pathlib import Path
from locale import strxfrm
from typing import Iterable

__all__ = ['PathCompletionEntry', 'PathCompletion', 'PathCompletionProvider', 'FileSystemPathCompletionProvider']


@functools.total_ordering
@dataclass
class PathCompletionEntry:
    display_name: str
    path: str
    is_dir: bool

    def __init__(self, name: str, path: str, is_dir: bool) -> None:
        self.display_name = f'{name}/' if is_dir else name
        self.path = path
        self.is_dir = is_dir

    def __lt__(self, other):
        if self.is_dir == other.is_dir:
            return strxfrm(self.display_name) < strxfrm(other.display_name)
        return other.is_dir < self.is_dir


class PathCompletionProvider:

    def get_completions(self, path) -> Iterable[PathCompletionEntry]:
        raise NotImplementedError()


class PathCompletion:

    def __init__(self, provider: PathCompletionProvider, show_files=True):
        self._provider = provider
        self._show_files = show_files

    def get_completions(self, path):
        results = []
        match_part = self._get_match_part(path)
        for entry in self._provider.get_completions(path):
            if self._entry_matches(entry, match_part):
                results.append(entry)

        return sorted(results)

    @staticmethod
    def complete(path, completion: PathCompletionEntry) -> str:
        dir_part, file_part = os.path.split(path)
        return os.path.join(dir_part, completion.display_name)

    @staticmethod
    def _get_match_part(path) -> str:
        dir_part, file_part = os.path.split(path)
        return file_part

    def _entry_matches(self, entry: PathCompletionEntry, pattern: str) -> bool:
        if not entry.display_name.startswith(pattern):
            return False
        if not entry.is_dir and not self._show_files:
            return False
        return True


class FileSystemPathCompletionProvider(PathCompletionProvider):

    def __init__(self, base_directory='.'):
        self._base_dir = Path(base_directory).expanduser().resolve(strict=True)
        if not self._base_dir.is_dir():
            raise OSError(f'Not a directory: {self._base_dir}')

    def set_base_directory(self, path):
        self._base_dir = Path(path).expanduser().resolve(strict=True)

    def get_completions(self, path) -> Iterable[PathCompletionEntry]:
        directory = self._resolve_directory(path)
        yield from self._scan_directory(directory)

    def _resolve_directory(self, path) -> Path:
        dir_part, file_part = os.path.split(path)
        dir_part = os.path.expanduser(dir_part)
        if not os.path.isabs(dir_part):
            dir_part = self._base_dir / dir_part
        return Path(dir_part).expanduser().resolve(strict=True)

    @staticmethod
    def _scan_directory(path):
        with os.scandir(path) as directory:
            for entry in directory:
                yield PathCompletionEntry(entry.name, entry.path, entry.is_dir())
