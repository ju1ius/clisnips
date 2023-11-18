

class ParsingError(Exception):
    ...


class CommandParsingError(ParsingError):
    def __init__(self, msg: str, cmd: str):
        super().__init__(msg)
        self.cmd = cmd


class DocumentationParsingError(ParsingError):
    def __init__(self, msg: str, doc: str):
        super().__init__(msg)
        self.doc = doc
