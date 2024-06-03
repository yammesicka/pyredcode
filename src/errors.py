class RedcodeError(Exception):
    pass


class ParseError(RedcodeError):
    def __init__(
        self, msg: str, line_index: int | None = None, line: str | None = None,
    ):
        self.msg = msg
        self.line = line
        self.line_index = line_index

    def __str__(self):
        if self.line is None:
            return self.msg
        return f"{self.msg} at line {self.line_index}: {self.line}"


class InvalidArgumentsLength(ParseError):
    pass


class InvalidOpcodeName(ParseError):
    pass


class EmptyCode(ParseError):
    pass


class OperandPrefixError(ParseError):
    pass


class OperandValueError(ParseError):
    pass


class PartialParseError(RedcodeError):
    def __init__(self, error: type[ParseError], msg: str):
        self.error = error
        self.msg = msg

    def to_exception(self, line_index: int, line: str) -> ParseError:
        return self.error(self.msg, line_index, line)


class SizeLimitExceeded(RedcodeError):
    pass


class RedcodeRuntimeError(RedcodeError):
    pass


class BadOpcode(RedcodeRuntimeError):
    pass


class BadModeForA(RedcodeRuntimeError):
    pass


class BadModeForB(RedcodeRuntimeError):
    pass


class RedcodeIndexError(RedcodeError):
    pass
