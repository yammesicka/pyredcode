import pytest

from src import memory
from src.instruction import Dat, Mode, Mov


@pytest.mark.parametrize("size", [256, 512, 1024])
def test_init_right_size(size):
    mem = memory.Memory(size)
    assert len(mem) == size


def test_init_initial_values():
    mem = memory.Memory(1024)
    assert all(x == Dat.of(0) for x in mem)


def test_allocate_effects_free_sections():
    mem = memory.Memory(1024)
    assert mem._free_sections == [memory.Sector(0, 1024)]
    mem.allocate([Dat.of(1)])
    assert mem._free_sections != [memory.Sector(0, 1024)]


def test_allocate_100_dats_takes_100_spaces():
    mem = memory.Memory(1024)
    for _ in range(100):
        mem.allocate([Dat.of(1)])
    assert sum(len(x) for x in mem._free_sections) == 1024 - 100


def test_allocate_100_movs_takes_100_spaces():
    mem = memory.Memory(1024)
    for _ in range(100):
        mem.allocate([Mov(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 0)])
    assert sum(len(x) for x in mem._free_sections) == 1024 - 100


def test_allocate_all_memory():
    mem = memory.Memory(1024)
    for _ in range(1024):
        mem.allocate([Dat.of(1)])
    assert len(mem._free_sections) == 0


def test_allocate_all_memory_plus_one_and_get_oom():
    mem = memory.Memory(1024)
    for _ in range(1024):
        mem.allocate([Dat.of(1)])
    with pytest.raises(memory.RedcodeRuntimeError):
        mem.allocate([Dat.of(1)])
