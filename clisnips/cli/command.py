from clisnips.dic import DependencyInjectionContainer


class Command:
    def __init__(self, dic: DependencyInjectionContainer):
        self.container = dic

    def run(self, argv) -> int:
        return NotImplemented

    def print(self, *args, stderr: bool = False, end: str = '\n', sep: str = ' '):
        self.container.markup_helper.print(*args, stderr=stderr, end=end, sep=sep)
