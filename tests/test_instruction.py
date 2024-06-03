import pytest

from src.instruction import (
    Dat,
    Instruction,
    Jmp,
    Mode,
    Mov,
)


def test_cast_int_zero():
    assert int(Dat(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 0)) == 0


def test_cast_int_one():
    assert int(Dat(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 1)) == 1


def test_init_jmp():
    assert Jmp(Mode.INDIRECT, 20)


def test_init_mov():
    assert Mov(Mode.INDIRECT, 20, Mode.IMMEDIATE, 5)


def test_cast_int_codewars_example():
    """This is the example from the official guide

    For further implementation details,
    see (CTRL+F "Encoded Integer"):
    https://corewar.co.uk/standards/cwg.txt
    """
    instruction = Mov(Mode.IMMEDIATE, 5, Mode.INDIRECT, 20)
    assert int(instruction) == 302010388


def test_cast_jmp_int_codewars_example():
    instruction = Jmp(Mode.RELATIVE, 113)
    assert int(instruction) == 4 * (2 ** 28) + 1 * (2 ** 24) + 113


def test_cast_strange_jmp_int_codewars_example():
    instruction = Jmp(Mode.INDIRECT, 50, Mode.RELATIVE, 113)
    assert int(instruction) == (
        4 * (2 ** 28) +   # Jmp opcode
        2 * (2 ** 26) +   # Mode A
        1 * (2 ** 24) +   # Mode B
        50 * (2 ** 12) +  # A
        113               # B
    )


@pytest.mark.parametrize(
    "instruction",
    [
        Dat(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 0),
        Dat(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 1),
        Dat(Mode.IMMEDIATE, 1),
        Mov(Mode.IMMEDIATE, 5, Mode.INDIRECT, 20),
        Jmp(Mode.INDIRECT, 20),
        Jmp(Mode.IMMEDIATE, 5, Mode.INDIRECT, 20),
    ],
)
def test_commutativity(instruction):
    """int(instruction) == instruction(int)"""
    int_instruction = int(instruction)
    assert int_instruction == int(Instruction.from_int(int_instruction))
