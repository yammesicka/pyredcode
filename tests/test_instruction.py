import pytest

from redcode.errors import BadMode, RedcodeRuntimeError
from redcode.instruction import (
    Add,
    Cmp,
    Dat,
    Djz,
    Instruction,
    Jmp,
    Jmz,
    Mode,
    Mov,
    Sub,
)
from redcode.memory import Memory
from src.redcode.instruction import InstructionResult
from src.redcode.machine import Machine


def test_cast_int_zero():
    assert int(Dat(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 0)) == 0


def test_cast_int_one():
    assert int(Dat(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 1)) == 1


def test_init_jmp():
    assert Jmp(Mode.INDIRECT, 20)


def test_init_mov():
    assert Mov(Mode.INDIRECT, 20, Mode.IMMEDIATE, 5)


def test_cast_int_corewars_example():
    """This is the example from the official guide

    For further implementation details,
    see (CTRL+F "Encoded Integer"):
    https://corewar.co.uk/standards/cwg.txt
    """
    instruction = Mov(Mode.IMMEDIATE, 5, Mode.INDIRECT, 20)
    assert int(instruction) == 302010388


def test_cast_jmp_int_corewars_example():
    instruction = Jmp(Mode.RELATIVE, 113)
    assert int(instruction) == 4 * (2 ** 28) + 1 * (2 ** 24) + 113


def test_cast_strange_jmp_int_corewars_example():
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
        Add(Mode.IMMEDIATE, 4, Mode.RELATIVE, 1),
        Mov(Mode.IMMEDIATE, 5, Mode.INDIRECT, 20),
        Jmp(Mode.INDIRECT, 20),
        Jmp(Mode.IMMEDIATE, 5, Mode.INDIRECT, 20),
    ],
)
def test_commutativity(instruction):
    """int(instruction) == instruction(int)"""
    int_instruction = int(instruction)
    assert instruction == Instruction.from_int(instruction)
    assert int_instruction == int(Instruction.from_int(int_instruction))


def test_signed_int():
    instruction = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, -1)
    assert instruction == Instruction.from_int(int(instruction))


def test_signed_big_int():
    instruction = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, -500000)
    expected = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, -500000)
    assert expected == Instruction.from_int(int(instruction))


def test_dat_run():
    instruction = Dat(Mode.IMMEDIATE, 0)
    with pytest.raises(RedcodeRuntimeError):
        instruction.run(0, Memory(1024))


def test_mov_fails_when_address_is_immediate():
    instruction = Mov(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 0)
    with pytest.raises(BadMode):
        instruction.run(0, Memory(1024))


def test_mov_run():
    memory = Memory(4)
    memory[0] = Mov(Mode.IMMEDIATE, 1, Mode.RELATIVE, 2)
    memory[1] = Jmp(Mode.IMMEDIATE, 0)
    assert (
        memory[0].run(0, memory) ==
        InstructionResult(new_ip=1, mem_index=2, mem_value=1)
    )
    assert memory[0] == Mov(Mode.IMMEDIATE, 1, Mode.RELATIVE, 2)
    assert memory[1] == Jmp(Mode.IMMEDIATE, 0)
    assert memory[2] == 1


def test_mov_run_with_instruction():
    memory = Memory(4)
    add = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, 0)
    memory[0] = Mov(Mode.RELATIVE, 1, Mode.RELATIVE, 2)
    memory[1] = add
    assert memory[0].run(0, memory) == InstructionResult(1, 2, int(add))
    assert memory[2] == add and type(memory[2]) is Add


def test_add_run_on_just_a_number():
    memory = Memory(4)
    memory[0] = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, 2)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    memory[3] = Dat.of(0)
    assert memory[0].run(0, memory) == InstructionResult(1, 2, 3)
    assert memory[2] == 3


def test_add_run_on_address():
    memory = Memory(4)
    add_1 = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, 0)
    memory[0] = add_1
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(1, 0, int(add_1) + 1)


def test_add_run_on_address_and_run_the_address():
    memory = Memory(4)
    add_1 = Add(Mode.IMMEDIATE, 1, Mode.RELATIVE, 0)
    memory[0] = add_1
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(1, 0, int(add_1) + 1)
    assert memory[0].run(0, memory) == InstructionResult(1, 1, 2)
    assert memory[1] == Dat.of(2)


def test_simple_sub():
    memory = Memory(4)
    sub_1 = Sub(Mode.IMMEDIATE, 1, Mode.RELATIVE, 1)
    memory[0] = sub_1
    memory[1] = Dat.of(2)
    memory[2] = Dat.of(1)
    assert memory[0].run(0, memory) == InstructionResult(1, 1, 1)
    assert memory[1] == 1


@pytest.mark.parametrize(
    "place,decrement,expected",
    [
        (0, 1, 1),
        (1, 1, 2),
        (2, 1, 3),
    ],
)
def test_sub_on_some_numbers(place, decrement, expected):
    memory = Memory(6)
    for i in range(4):
        memory[i] = Dat.of(i + 1)
    memory[place] = Sub(Mode.IMMEDIATE, decrement, Mode.RELATIVE, 1)
    result = memory[place].run(place, memory)
    expected_ir = InstructionResult(place + 1, place + 1, expected)
    assert result == expected_ir
    assert memory[place + 1] == expected


def test_simple_jmp():
    memory = Memory(4)
    memory[0] = Jmp(Mode.RELATIVE, 2)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(2, None, None)


def test_out_of_bound_jmp():
    memory = Memory(4)
    memory[0] = Jmp(Mode.RELATIVE, 100)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(0, None, None)


def test_jmz():
    memory = Memory(4)
    memory[0] = Jmz(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 2)
    memory[1] = Dat.of(0)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(2, None, None)


def test_jmz_not_zero():
    memory = Memory(4)
    memory[0] = Jmz(Mode.IMMEDIATE, 1, Mode.IMMEDIATE, 2)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(1, None, None)


def teset_djz():
    memory = Memory(4)
    memory[0] = Djz(Mode.IMMEDIATE, 1, Mode.IMMEDIATE, 2)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(1, 0, 0)


def test_djz_zero():
    memory = Memory(4)
    memory[0] = Djz(Mode.RELATIVE, 1, Mode.IMMEDIATE, 2)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(2, 1, 0)


def test_djz_not_zero():
    memory = Memory(4)
    memory[0] = Djz(Mode.RELATIVE, 1, Mode.IMMEDIATE, 2)
    memory[1] = Dat.of(3)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(1, 1, 2)


def test_cmp_not_equal():
    memory = Memory(4)
    memory[0] = Cmp(Mode.IMMEDIATE, 1, Mode.IMMEDIATE, 2)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(1, None, None)


def test_cmp_equal():
    memory = Memory(4)
    memory[0] = Cmp(Mode.IMMEDIATE, 1, Mode.IMMEDIATE, 1)
    memory[1] = Dat.of(1)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(2, None, None)


def test_cmp_equal_relative():
    memory = Memory(4)
    memory[0] = Cmp(Mode.RELATIVE, 1, Mode.RELATIVE, 2)
    memory[1] = Dat.of(2)
    memory[2] = Dat.of(2)
    assert memory[0].run(0, memory) == InstructionResult(2, None, None)


def test_jmp_relative():
    machine = Machine(4, allow_single_process=True)
    machine.load_code("""
        JMP 2
        DAT #0
        MOV #2, -1
        JMP -3
    """, "")
    machine.run()
    assert machine.memory[1] == Dat.of(2)


def test_indirect():
    machine = Machine(3, allow_single_process=True)
    machine.load_code("""
        ; Use dwarf to test indirect addressing
        MOV #2, 5
        MOV #8, @1
        DAT #0     ; placeholder, will hold 5
    """, "")
    machine.run()
    assert machine.memory[1] == Dat.of(8)
