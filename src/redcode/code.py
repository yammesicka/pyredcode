from typing import NamedTuple

from redcode.config import MAX_PROGRAM_SIZE, COMMENT_SIGN
from redcode.errors import (
    EmptyCode, InvalidArgumentsLength, InvalidOpcodeName, OperandPrefixError,
    OperandValueError, ParseError, PartialParseError, SizeLimitExceeded,
)
from redcode.instruction import Instruction, Mode


class Line(NamedTuple):
    id: int
    content: str


def try_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise PartialParseError(OperandValueError, f"Bad {value=}")


class Parser:
    def __init__(
        self,
        code: str,
        instruction_limit: int | None = MAX_PROGRAM_SIZE,
    ):
        self.code = self.basic_cleanup(code)
        if not Validator(code).is_valid():
            raise ParseError("Invalid code, be sure to run Validator first")
        self.instructions = []
        self._max_size = instruction_limit  # Pass None to disable

    @classmethod
    def basic_cleanup(cls, code: str) -> list[str]:
        stripped = code.strip()
        splitted = cls.code_to_lines(stripped)
        clean = cls.remove_comments(splitted)
        return clean

    @staticmethod
    def code_to_lines(code: str) -> list[str]:
        return code.splitlines()

    @staticmethod
    def remove_comments(code):
        return [line.partition(COMMENT_SIGN)[0] for line in code]

    @staticmethod
    def command(opcode_name: str) -> type[Instruction]:
        try:
            instruction = Instruction.get(opcode_name)
        except KeyError:
            raise PartialParseError(InvalidOpcodeName, f"Bad {opcode_name=}")
        else:
            return instruction

    @staticmethod
    def operand(operand: str) -> tuple[Mode, int]:
        if operand[0] == "#":
            return Mode.IMMEDIATE, try_int(operand[1:])
        elif operand[0] == "@":
            return Mode.INDIRECT, try_int(operand[1:])
        elif operand.replace("-", "").isdecimal():
            return Mode.RELATIVE, try_int(operand)
        else:
            raise PartialParseError(OperandPrefixError, f"Bad {operand=}")

    def parse_instruction(self, line: Line):
        params = [p.strip(",") for p in line.content.split() if p]
        opcode = self.command(params[0])
        operands = []
        for param in params[1:]:
            operands.extend(self.operand(param))
        return opcode(*operands)

    def parse(self) -> list[Instruction]:
        for i, line in enumerate(self.code, 1):
            if not line:
                continue
            parsed = self.parse_instruction(Line(i, line))
            self.instructions.append(parsed)

        size = len(self.instructions)
        if self._max_size is not None and size > self._max_size:
            raise SizeLimitExceeded(
                f"Program size exceeded: {size} > {self._max_size}"
            )

        return self.instructions


class Validator:
    def __init__(self, code: str):
        self.code = Parser.basic_cleanup(code)
        self._exceptions: list[ParseError] = []

    def _check_args_length(self, line: Line, params: list[str]):
        if len(params) <= 1 or len(params) > 3:
            raise InvalidArgumentsLength(
                f"Invalid number of arguments {params}", *line,
            )

    def _check_valid_opcode(self, opcode: str):
        _ = Parser.command(opcode)

    def _check_params_length_for_opcode(
        self, line: Line, opcode: str, params: list[str],
    ):
        expected = len(Instruction.get(opcode).ARGUMENTS)
        got = len(params)
        if expected != got:
            raise InvalidArgumentsLength(
                f"Invalid number of arguments {params} for {opcode}", *line,
            )

    def _check_argument_validity(self, arg: str):
        _ = Parser.operand(arg)

    def _parse_instruction(self, line: Line):
        params = [p.strip(",") for p in line.content.split() if p]
        self._check_args_length(line, params)
        self._check_valid_opcode(params[0])
        self._check_params_length_for_opcode(line, params[0], params[1:])
        for param in params[1:]:
            self._check_argument_validity(param)

    @property
    def errors(self) -> list[ParseError]:
        return self._exceptions

    def _run(self):
        lines = Parser.remove_comments(self.code)
        if ''.join(lines).strip() == "":
            self._exceptions.append(EmptyCode("Empty code"))
            return None

        for i, line in enumerate(lines, 1):
            if not line:
                continue
            try:
                self._parse_instruction(Line(i, line))
            except ParseError as e:
                self._exceptions.append(e)
            except PartialParseError as e:
                self._exceptions.append(e.to_exception(i, line))

    def is_valid(self) -> bool:
        try:
            self._exceptions = []
            self._run()
        except ParseError:
            return False
        else:
            return not self._exceptions
