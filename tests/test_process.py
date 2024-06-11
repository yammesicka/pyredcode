import pytest

from redcode.errors import DatError, RedcodeRuntimeError
from redcode.instruction import Add, Dat, Jmp, Mode, Mov
from redcode.memory import Memory
from redcode.process import Process


def test_process_ticks_without_crashing(code):
    m = Memory(64)
    code_start = m.allocate(code)
    process = Process(0, code_start, m)
    process.tick()


def test_process_tick_performs_mov():
    m = Memory(2)
    code_start = m.allocate([
        Mov(Mode.IMMEDIATE, 50, Mode.RELATIVE, 1),
    ])
    process = Process(0, code_start, m)
    process.tick()
    assert m[code_start + 1] == 50


def test_process_tick_performs_signed_mov():
    m = Memory(2)
    m[0] = Dat.of(20)
    m[1] = Dat.of(20)
    code_start = m.allocate([
        Mov(Mode.IMMEDIATE, -1, Mode.RELATIVE, 1),
    ])
    process = Process(0, code_start, m)
    process.tick()
    assert m.safely_read_int(code_start + 1) == -1


def test_mov_dat_to_rel_1_tick_goes_kaboom():
    m = Memory(2)
    m[0] = Dat.of(20)
    m[1] = Dat.of(20)
    code_start = m.allocate([
        Mov(Mode.IMMEDIATE, 1, Mode.RELATIVE, 1),
    ])
    process = Process(0, code_start, m)
    process.tick()
    assert process.is_alive
    process.tick()
    assert not process.is_alive


def test_process_imp():
    m = Memory(5)
    m[0] = Dat.of(20)
    m[1] = Dat.of(20)
    imp = Mov(Mode.RELATIVE, 0, Mode.RELATIVE, 1)
    code_start = m.allocate([imp])
    process = Process(0, code_start, m)
    for _ in range(20):
        assert process.is_alive
        process.tick()
    assert all(m[i] == imp for i in range(5))
