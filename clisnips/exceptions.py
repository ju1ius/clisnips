

class ParsingError(Exception):

    @classmethod
    def from_exception(cls, err: Exception, msg: str = ''):
        err_msg = err.args[0] if len(err.args) else str(err)
        msg = f'{msg} {err_msg}' if msg else err_msg
        return cls(msg)
