import pytest

from src import config
from src.instruction import Dat, Instruction
from src.machine import Machine


@pytest.mark.parametrize("memory_size", [0, -5])
def test_set_bad_machine_memory_init(memory_size):
    with pytest.raises(ValueError):
        Machine(memory_size)


@pytest.mark.parametrize("memory_size", [10, 1024, 2048])
def test_allocation(memory_size):
    machine = Machine(memory_size)
    assert len(machine) == memory_size


def test_default_allocation():
    machine = Machine()
    assert len(machine) == config.MEMORY_SIZE


def test_read_address_after_init():
    machine = Machine()
    assert machine[0] == Dat.of(0)


@pytest.mark.parametrize("memory_size", [10, 1024, 2048])
def test_read_last_address_after_init(memory_size):
    machine = Machine(memory_size)
    assert machine[memory_size - 1] == Dat.of(0)


@pytest.mark.parametrize("memory_size", [10, 1024, 2048])
def test_read_out_of_index_address_do_not_fails(memory_size):
    machine = Machine(memory_size)
    assert machine[memory_size]


def test_set_address_after_init():
    machine = Machine()
    machine[0] = Instruction.from_int(1)
    assert machine[0] == 1


@pytest.mark.parametrize("memory_size", [10, 1024, 2048])
def test_set_last_address_after_init(memory_size):
    machine = Machine(memory_size)
    machine[memory_size - 1] = Instruction.from_int(1)
    assert machine[memory_size - 1] == 1


@pytest.mark.parametrize("memory_size", [10, 1024, 2048])
def test_set_still_works_when_set_out_of_index(memory_size):
    machine = Machine(memory_size)
    machine[memory_size] = Instruction.from_int(1)
