from typing import NewType

from src.errors import BadOpcode, BadModeForA, BadModeForB


ModeType = NewType("ModeType", int)
ArgType = NewType("ArgType", int)


class Mode:
    IMMEDIATE = ModeType(0)  # Symbol: #
    RELATIVE = ModeType(1)
    INDIRECT = ModeType(2)  # Symbol: @

    @classmethod
    def values(cls):
        return [cls.IMMEDIATE, cls.RELATIVE, cls.INDIRECT]


class Arguments:
    A = ArgType(0)
    B = ArgType(1)


class Instruction:
    OPCODE = -1
    ARGUMENTS = []

    _classes = {}
    _opcodes = {}

    def __init__(
        self, mode_a: ModeType, a: int, mode_b: ModeType, b: int,
    ):
        self._name = self.__class__.__name__
        self._opcode = self.OPCODE
        self.mode_a = int(mode_a)
        self.a = int(a)
        self.mode_b = int(mode_b)
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
    def from_int(cls, integer: int) -> "Instruction":
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

    def __str__(self):
        return f"{self._name}({self.a}, {self.b})"

    def __int__(self):
        return (
            (self._opcode << 28) |
            (self.mode_a << 26) |
            (self.mode_b << 24) |
            (self.a << 12) |
            (self.b)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Instruction):
            raise NotImplementedError(
                f"right operand {other=} is not an Instruction: {type(other)=}"
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
        mode_a: ModeType,
        a: int | None = None,
        mode_b: ModeType | None = None,
        b: int | None = None,
    ):
        # Arrange arguments
        if mode_b is None and b is None:
            if mode_a is not None and a is None:
                mode_a, a = Mode.RELATIVE, mode_a
            b, mode_b = a, mode_a
            a, mode_a = 0, ModeType(0)
        if mode_b is None:
            mode_b = ModeType(1)

        assert a is not None and b is not None
        super().__init__(mode_a, a, mode_b, b)


class Dat(SingleArgInstruction):
    OPCODE = 0
    ARGUMENTS = [Arguments.B]

    @classmethod
    def of(cls, value: int) -> "Dat":
        return Dat(Mode.IMMEDIATE, value)


class Mov(Instruction):
    OPCODE = 1
    ARGUMENTS = [Arguments.A, Arguments.B]


class Add(Instruction):
    OPCODE = 2
    ARGUMENTS = [Arguments.A, Arguments.B]


class Sub(Instruction):
    OPCODE = 3
    ARGUMENTS = [Arguments.A, Arguments.B]


class Jmp(SingleArgInstruction):
    OPCODE = 4
    ARGUMENTS = [Arguments.B]


class Jmz(Instruction):
    OPCODE = 5
    ARGUMENTS = [Arguments.A, Arguments.B]


class Djz(Instruction):
    OPCODE = 6
    ARGUMENTS = [Arguments.A, Arguments.B]


class Cmp(Instruction):
    OPCODE = 7
    ARGUMENTS = [Arguments.A, Arguments.B]
