import pytest

from redcode import config
from redcode.instruction import Dat, Instruction
from redcode.machine import Machine


@pytest.mark.parametrize("memory_size", [0, -5])
def test_set_bad_machine_memory_init(memory_size):
    with pytest.raises(ValueError):
        Machine(memory_size)


@pytest.mark.parametrize("memory_size", [10, 1024, 2048])
def test_allocation(memory_size):
    machine = Machine(memory_size)
    assert len(machine.memory) == memory_size


def test_default_allocation():
    machine = Machine()
    assert len(machine.memory) == config.MEMORY_SIZE


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


def test_right_process_ids():
    machine = Machine(1024)
    assert machine.processes == []
    for i in range(10):
        machine.load_code("DAT #0", f"Player {i}")
    process_ids = [p._id for p in machine.processes]
    assert process_ids == list(range(10))


def test_right_process_ids_multiple_machines():
    machine = Machine(1024)
    assert machine.processes == []
    for i in range(10):
        machine.load_code("DAT #0", f"Player {i}")
    process_ids = [p._id for p in machine.processes]
    assert process_ids == list(range(10))

    machine = Machine(5)
    assert machine.processes == []
    machine.load_code("DAT #0", "Player 1")
    process_ids = [p._id for p in machine.processes]
    assert process_ids == [0]
