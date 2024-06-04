from enum import IntEnum
from typing import TYPE_CHECKING, NewType

from src.errors import BadOpcode, BadModeForA, BadModeForB, DatError


if TYPE_CHECKING:
    from src.memory import Memory


ModeType = NewType("ModeType", int)
ArgType = NewType("ArgType", int)


class Mode(IntEnum):
    IMMEDIATE = ModeType(0)
    RELATIVE = ModeType(1)
    INDIRECT = ModeType(2)

    @classmethod
    def values(cls):
        return [cls.IMMEDIATE, cls.RELATIVE, cls.INDIRECT]

    def __str__(self) -> str:
        return {
            self.IMMEDIATE: "#",
            self.RELATIVE: "",
            self.INDIRECT: "@",
        }[self]


class Arguments:
    A = ArgType(0)
    B = ArgType(1)


class Instruction:
    OPCODE = -1
    ARGUMENTS = []

    _classes = {}
    _opcodes = {}

    def __init__(
        self, mode_a: Mode, a: int, mode_b: Mode, b: int,
    ):
        self.name = self.__class__.__name__.upper()
        self.opcode = self.OPCODE
        self.mode_a = mode_a
        self.a = int(a)
        self.mode_b = mode_b
        self.b = int(b)

    def __init_subclass__(cls) -> None:
        cls._classes[cls.__name__.upper()] = cls
        cls._opcodes[cls.OPCODE] = cls

    @classmethod
    def get(cls, opcode_name: str) -> type["Instruction"]:
        return cls._classes[opcode_name.upper()]

    @classmethod
    def get_all_opcode_names(cls) -> set[str]:
        return set(cls._classes.keys())

    @classmethod
    def from_int(cls, integer: "int | Instruction") -> "Instruction":
        if not isinstance(integer, int):
            integer = int(integer)

        opcode = (integer >> 28) & 0b1111
        if opcode not in cls._opcodes:
            raise BadOpcode(opcode)

        mode_a = (integer >> 26) & 0b11
        if mode_a not in Mode.values():
            raise BadModeForA(mode_a)

        mode_b = (integer >> 24) & 0b11
        if mode_b not in Mode.values():
            raise BadModeForB(mode_b)

        a = (integer >> 12) & ((1 << 12) - 1)  # 12 bits
        b = integer & ((1 << 12) - 1)          # 12 bits
        return cls._opcodes[opcode](mode_a, a, mode_b, b)

    def run(self, ip: int, memory: "Memory") -> int:
        raise NotImplementedError(
            f"`run` not implemented for {self.__class__.__name__}"
        )

    def __str__(self):
        opcode_name = self.name.upper()
        a = f"{Mode(self.mode_a)}{self.a}"
        b = f"{Mode(self.mode_b)}{self.b}"
        return f"{opcode_name} {a}, {b}"

    def __int__(self):
        return (
            (self.opcode << 28) |
            (self.mode_a << 26) |
            (self.mode_b << 24) |
            (self.a << 12) |
            (self.b)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Instruction, int)):
            raise NotImplementedError(
                f"Can't compare {other=} with {type(other)=}"
            )
        return int(self) == int(other)

    def __repr__(self):
        mode_a = f"{self.mode_a}"
        a = f"{self.a}"
        mode_b = f"{self.mode_b}"
        b = f"{self.b}"
        return (
            f"{self.__class__.__name__}("
            f"{mode_a=!r}, "
            f"{a=!r}, "
            f"{mode_b=!r}, "
            f"{b=!r}, "
            ")"
        )


class SingleArgInstruction(Instruction):
    def __init__(
        self,
        mode_a: Mode,
        a: int | None = None,
        mode_b: Mode | None = None,
        b: int | None = None,
    ):
        # Arrange arguments
        if mode_b is None and b is None:
            if mode_a is not None and a is None:
                mode_a, a = Mode.RELATIVE, mode_a
            b, mode_b = a, mode_a
            a, mode_a = 0, Mode.IMMEDIATE
        if mode_b is None:
            mode_b = Mode.RELATIVE

        assert a is not None and b is not None
        super().__init__(mode_a, a, mode_b, b)


# TODO: I don't like the fact that the instruction know about
#       the memory object. Refactor the instructions to return:
#       Action([list_of_memory_changes], new_ip)

class Dat(SingleArgInstruction):
    """Data instruction, don't run it, you'll die"""
    OPCODE = 0
    ARGUMENTS = [Arguments.B]

    @classmethod
    def of(cls, value: int) -> "Dat":
        return Dat(Mode.IMMEDIATE, value)

    def run(self, ip: int, memory: "Memory") -> int:
        raise DatError("DAT instruction encountered")


class Mov(Instruction):
    """Move op_a to op_b"""
    OPCODE = 1
    ARGUMENTS = [Arguments.A, Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        op_a = memory.value(self.mode_a, self.a, ip)
        addr_b = memory.address(self.mode_b, self.b, ip)
        memory[addr_b] = op_a
        return (ip + 1) % len(memory)


class Add(Instruction):
    """Add op_a to op_b and store it in op_b"""
    OPCODE = 2
    ARGUMENTS = [Arguments.A, Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        op_a = memory.value(self.mode_a, self.a, ip)
        op_b = memory.value(self.mode_b, self.b, ip)
        address_b = memory.address(self.mode_b, self.b, ip)
        memory[address_b] = int(op_a) + int(op_b)
        return (ip + 1) % len(memory)


class Sub(Instruction):
    """Subtract op_b from op_a and store it in op_b"""
    OPCODE = 3
    ARGUMENTS = [Arguments.A, Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        op_a = memory.value(self.mode_a, self.a, ip)
        op_b = memory.value(self.mode_b, self.b, ip)
        address_b = memory.address(self.mode_b, self.b, ip)
        memory[address_b] = int(op_b) - int(op_a)
        return (ip + 1) % len(memory)


class Jmp(SingleArgInstruction):
    """Jump to op_b"""
    OPCODE = 4
    ARGUMENTS = [Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        return int(memory.value(self.mode_b, self.b, ip)) % len(memory)


class Jmz(Instruction):
    """If op_a == 0, jump to op_b"""
    OPCODE = 5
    ARGUMENTS = [Arguments.A, Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        op_a = memory.value(self.mode_a, self.a, ip)
        op_b = memory.value(self.mode_b, self.b, ip)
        if op_a == 0:
            return int(op_b) % len(memory)
        return (ip + 1) % len(memory)


class Djz(Instruction):
    """Decrement op_a and store it. If answer is 0, jump to op_b"""
    OPCODE = 6
    ARGUMENTS = [Arguments.A, Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        address_a = memory.address(self.mode_a, self.a, ip)
        op_a = memory.value(self.mode_a, self.a, ip)
        op_b = memory.value(self.mode_b, self.b, ip)
        answer = int(op_a) - 1
        memory[address_a] = answer
        if answer == 0:
            return int(op_b) % len(memory)
        return (ip + 1) % len(memory)


class Cmp(Instruction):
    """If op_a == op_b, skip the next instruction"""
    OPCODE = 7
    ARGUMENTS = [Arguments.A, Arguments.B]

    def run(self, ip: int, memory: "Memory") -> int:
        op_a = memory.value(self.mode_a, self.a, ip)
        op_b = memory.value(self.mode_b, self.b, ip)
        if op_a == op_b:
            return (ip + 2) % len(memory)
        return (ip + 1) % len(memory)
