import pytest

from clisnips.utils.path_completion import (
    FileAttributes as FA,
)
from clisnips.utils.path_completion import (
    FileSystemPathCompletionProvider,
    PathCompletion,
    PathCompletionEntry,
    PathCompletionProvider,
)


class StubProvider(PathCompletionProvider):
    def __init__(self, results):
        self._results = results

    def get_completions(self, path):
        return self._results


class TestCompletionEntry:
    def test_dirname_ends_with_slash(self):
        entry = PathCompletionEntry('foo', '/usr/share/foo', FA.IS_DIR)
        assert 'foo/' == entry.display_name

        entry = PathCompletionEntry('foo', '/usr/share/foo', FA.IS_FILE)
        assert 'foo' == entry.display_name

    def test_it_sorts_alphabetically(self):
        entries = [
            PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_FILE),
            PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
            PathCompletionEntry('baffle', '/foo/bar/baffle', FA.IS_FILE),
            PathCompletionEntry('woot', '/foo/bar/woot', FA.IS_FILE),
        ]
        expected = [
            PathCompletionEntry('baffle', '/foo/bar/baffle', FA.IS_FILE),
            PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
            PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_FILE),
            PathCompletionEntry('woot', '/foo/bar/woot', FA.IS_FILE),
        ]
        assert expected == sorted(entries)

    def test_it_sorts_directories_first(self):
        entries = [
            PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_DIR),
            PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
            PathCompletionEntry('waffle', '/foo/bar/waffle', FA.IS_DIR),
            PathCompletionEntry('woot', '/foo/bar/woot', FA.IS_FILE),
        ]
        expected = [
            PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_DIR),
            PathCompletionEntry('waffle', '/foo/bar/waffle', FA.IS_DIR),
            PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
            PathCompletionEntry('woot', '/foo/bar/woot', FA.IS_FILE),
        ]
        assert expected == sorted(entries)


class TestPathCompletion:
    def test_simple_filename_completion(self):
        path = '/foo/bar/ba'
        provider = StubProvider(
            [
                PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
                PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_FILE),
                PathCompletionEntry('baffle', '/foo/bar/baffle', FA.IS_FILE),
                PathCompletionEntry('woot', '/foo/bar/woot', FA.IS_FILE),
            ]
        )
        completion = PathCompletion(provider)
        expected = [
            PathCompletionEntry('baffle', '/foo/bar/baffle', FA.IS_FILE),
            PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
            PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_FILE),
        ]
        assert expected == completion.get_completions(path)
        assert '/foo/bar/baz' == completion.complete(path, expected[1])

    def test_simple_dirname_completion(self):
        path = '/foo/bar/'
        expected = [
            PathCompletionEntry('woot', '/foo/bar/woot', FA.IS_DIR),
            PathCompletionEntry('baz', '/foo/bar/baz', FA.IS_FILE),
            PathCompletionEntry('bazar', '/foo/bar/bazar', FA.IS_FILE),
        ]
        provider = StubProvider(expected)
        completion = PathCompletion(provider)
        assert expected == completion.get_completions(path)
        assert '/foo/bar/bazar' == completion.complete(path, expected[2])

    def test_root_directory_completion(self):
        path = '/'
        expected = [
            PathCompletionEntry('bin', '/bin', FA.IS_DIR),
            PathCompletionEntry('usr', '/usr', FA.IS_DIR),
            PathCompletionEntry('vmlinuz', '/vmlinuz', FA.IS_FILE),
        ]
        provider = StubProvider(expected)
        completion = PathCompletion(provider)
        assert expected == completion.get_completions(path)
        assert '/usr/' == completion.complete(path, expected[1])

    def test_home_directory_completion(self):
        path = '~/'
        expected = [
            PathCompletionEntry('.config', '/home/user/.config', FA.IS_DIR),
            PathCompletionEntry('.bashrc', '/home/user/.bashrc', FA.IS_FILE),
        ]
        provider = StubProvider(expected)
        completion = PathCompletion(provider)
        assert expected == completion.get_completions(path)
        assert '~/.config/' == completion.complete(path, expected[0])

    def test_no_directory_completion(self):
        path = 'ba'
        provider = StubProvider(
            [
                PathCompletionEntry('bar', '/home/user/bar/', FA.IS_DIR),
                PathCompletionEntry('baz', '/home/user/baz', FA.IS_FILE),
                PathCompletionEntry('qux', '/home/user/qux', FA.IS_FILE),
            ]
        )
        completion = PathCompletion(provider)
        expected = [
            PathCompletionEntry('bar', '/home/user/bar/', FA.IS_DIR),
            PathCompletionEntry('baz', '/home/user/baz', FA.IS_FILE),
        ]
        assert expected == completion.get_completions(path)
        assert 'bar/' == completion.complete(path, expected[0])


@pytest.mark.usefixtures('fs')
class TestFileSystemCompletionProvider:
    def test_simple_absolute_paths(self, fs):
        expected = []
        for name in ('foo', 'bar', 'baz', 'qux'):
            name = f'{name}.so'
            path = f'/usr/lib/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider()
        completions = list(provider.get_completions('/usr/lib/ba'))
        assert expected == completions

    def test_simple_relative_paths(self, fs):
        expected = []
        for name in ('foo', 'bar', 'baz', 'qux'):
            name = f'{name}.so'
            path = f'/usr/lib/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider('/usr/lib')
        completions = list(provider.get_completions('ba'))
        assert expected == completions

    def test_dot_relative_paths(self, fs):
        expected = []
        for name in ('foo', 'bar', 'baz', 'qux'):
            name = f'{name}.so'
            path = f'/usr/lib/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider('/usr/lib')
        completions = list(provider.get_completions('./ba'))
        assert expected == completions

    def test_dot_dot_relative_paths(self, fs):
        base_dir = '/usr/lib/X11'
        expected = [
            PathCompletionEntry('X11', base_dir, FA.IS_DIR),
        ]
        fs.create_dir(base_dir)
        for name in ('foo', 'bar', 'baz', 'qux'):
            name = f'{name}.so'
            path = f'/usr/lib/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider(base_dir)
        completions = list(provider.get_completions('../ba'))
        assert expected == completions

    def test_user_relative_paths(self, fs, monkeypatch):
        monkeypatch.setenv('HOME', '/home/bigmonkey')
        expected = []
        for name in ('foo', 'bar', 'baz', 'qux'):
            name = f'{name}.txt'
            path = f'/home/bigmonkey/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider()
        completions = list(provider.get_completions('~/ba'))
        assert expected == completions

    def test_directory_paths(self, fs):
        expected = []
        for name in ('foo', 'bar', 'baz', 'qux'):
            path = f'/bin/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider()
        completions = list(provider.get_completions('/bin/'))
        assert expected == completions

    def test_root_directory_paths(self, fs):
        expected = [
            # added by pyfakefs
            PathCompletionEntry('tmp', '/tmp', FA.IS_DIR),
        ]
        for name in ('foo', 'bar', 'baz', 'qux'):
            path = f'/{name}'
            fs.create_file(path)
            expected.append(PathCompletionEntry(name, path, FA.IS_FILE))
        provider = FileSystemPathCompletionProvider()
        completions = list(provider.get_completions('/'))
        assert expected == completions

    def test_it_fails_when_base_directory_does_not_exist(self, fs):
        with pytest.raises(FileNotFoundError):
            FileSystemPathCompletionProvider('/non_existent_file.example')

    def test_it_fails_when_base_directory_is_not_a_directory(self, fs):
        fs.create_file('/foo/bar')
        with pytest.raises(OSError):
            FileSystemPathCompletionProvider('/foo/bar')

    def test_it_fails_when_home_does_not_exist(self, fs):
        with pytest.raises(OSError):
            FileSystemPathCompletionProvider('~fake_user')
