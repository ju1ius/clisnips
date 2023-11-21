class ParseError(Exception):
    ...


class CommandParseError(ParseError):
    def __init__(self, msg: str, cmd: str):
        super().__init__(msg)
        self.cmd = cmd


class DocumentationParseError(ParseError):
    def __init__(self, msg: str):
        super().__init__(msg)
