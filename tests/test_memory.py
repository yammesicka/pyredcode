import pytest

from redcode import memory
from redcode.errors import RedcodeOutOfMemoryError
from redcode.memory import Memory, Sector, Sectors
from redcode.instruction import Dat, Instruction, Jmp, Mode, Mov


@pytest.mark.parametrize("size", [256, 512, 1024])
def test_init_right_size(size):
    mem = Memory(size)
    assert len(mem) == size


def test_init_initial_values():
    mem = Memory(1024)
    assert all(x == Dat.of(0) for x in mem)


def test_allocate_returns_index():
    mem = Memory(1)
    allocated_address = mem.allocate([Dat.of(1)])
    assert allocated_address == 0


def test_allocate_2_returns_index():
    mem = Memory(2)
    allocated_address = mem.allocate([Dat.of(1), Dat.of(2)])
    assert allocated_address == 0


@pytest.mark.parametrize(
    "code",
    [
        [Dat.of(5)],
        [Dat.of(5), Dat.of(2)],
        [Dat.of(1), Dat.of(2), Dat.of(3)],
    ],
)
def test_allocate_dats_creates_right_code_in_memory(code):
    mem = Memory(len(code))
    allocated_address = mem.allocate(code)
    assert allocated_address == 0
    for i in range(len(code)):
        assert mem[i] == code[i]


@pytest.mark.parametrize(
    "code",
    [
        [Mov(Mode.IMMEDIATE, 0, Mode.RELATIVE, 1)],
        [Jmp(Mode.RELATIVE, 1)],
    ],
)
def test_allocate_creates_right_instruction_in_memory(code):
    mem = Memory(len(code))
    allocated_address = mem.allocate(code)
    assert allocated_address == 0
    for i in range(len(code)):
        assert mem[i] == code[i]


@pytest.mark.parametrize(
    "code",
    [
        [Mov(Mode.IMMEDIATE, 0, Mode.RELATIVE, 1), Jmp(Mode.RELATIVE, 1)],
        [Jmp(Mode.RELATIVE, 1), Mov(Mode.IMMEDIATE, 0, Mode.RELATIVE, 1)],
        [Mov(Mode.IMMEDIATE, 0, Mode.RELATIVE, 1), Mov(Mode.IMMEDIATE, 0, Mode.RELATIVE, 1)],
    ],
)
def test_allocate_creates_right_code_in_memory(code):
    mem = Memory(len(code))
    allocated_address = mem.allocate(code)
    assert allocated_address == 0
    for i in range(len(code)):
        assert mem[i] == code[i]


def test_allocate_program_effects_free_sections():
    mem = Memory(1024)
    assert mem._free == Sectors([Sector(0, 1024)])
    mem.allocate([Dat.of(1)], override=False)
    assert mem._free != [Sector(0, 1024)]


def test_allocate_program_100_dats_takes_100_spaces():
    mem = Memory(1024)
    for _ in range(100):
        mem.allocate([Dat.of(1)], override=False)
    assert len(mem._free) == 1024 - 100


def test_allocate_program_100_movs_takes_100_spaces():
    mem = Memory(1024)
    for _ in range(100):
        instructions = [Mov(Mode.IMMEDIATE, 0, Mode.IMMEDIATE, 0)]
        mem.allocate(instructions, override=False)  # type: ignore
    assert sum(len(x) for x in mem._free) == 1024 - 100


def test_allocate_program_all_memory():
    mem = Memory(1024)
    for _ in range(1024):
        mem.allocate([Dat.of(1)], override=False)
    assert len(mem._free) == 0


def test_allocate_program_all_memory_plus_one_and_get_oom():
    mem = Memory(1024)
    for _ in range(1024):
        mem.allocate([Dat.of(1)], override=False)
    with pytest.raises(RedcodeOutOfMemoryError):
        mem.allocate([Dat.of(1)], override=False)


def test_allocate_with_override_is_always_allowed():
    mem = Memory(4)
    for _ in range(1024 * 10):
        mem.allocate([Dat.of(1)])
    assert mem._free == Sectors([])


def test_allocate_with_override_cant_be_bigger_than_memory():
    mem = Memory(4)
    mem.allocate([Dat.of(1)] * 4)
    with pytest.raises(RedcodeOutOfMemoryError):
        mem.allocate([Dat.of(1)] * 5)


@pytest.mark.parametrize("sector,expected", [
    (Sector(0, 10), 10),
    (Sector(10, 20), 10),
    (Sector(0, 20), 20),
    (Sector(0, 1), 1),
])
def test_sector_len(sector, expected):
    assert len(sector) == expected


@pytest.mark.parametrize("sector,expected", [
    ((-1, 10), ValueError),
    ((10, -1), ValueError),
    ((10, 2), ValueError),
    ((0, 0), ValueError),
])
def test_sector_bad_init(sector, expected):
    with pytest.raises(expected):
        Sector(*sector)


@pytest.mark.parametrize("sector_a,sector_b,expected", [
    ((1, 10), (2, 5), (2, 5)),
    ((1, 10), (0, 14), (1, 10)),
    ((2, 5), (1, 10), (2, 5)),
    ((0, 14), (1, 10), (1, 10)),
    ((0, 10), (10, 20), None),
    ((10, 20), (0, 10), None),
    ((0, 10), (5, 15), (5, 10)),
    ((5, 15), (0, 10), (5, 10)),
    ((0, 1), (5, 10), None),
    ((5, 10), (0, 1), None),
])
def test_sector_and_operation(sector_a, sector_b, expected):
    new_sector = Sector(*sector_a) & Sector(*sector_b)
    expected_sector = Sector(*expected) if expected else None
    assert new_sector == expected_sector


@pytest.mark.parametrize("sector_a,sector_b,expected", [
    ((1, 10), (2, 5), [(1, 2), (5, 10)]),
    ((1, 10), (0, 14), []),
    ((2, 5), (1, 10), []),
    ((0, 14), (1, 10), [(0, 1), (10, 14)]),
    ((0, 10), (10, 20), [(0, 10)]),
    ((10, 20), (0, 10), [(10, 20)]),
    ((0, 10), (5, 15), [(0, 5)]),
    ((5, 15), (0, 10), [(10, 15)]),
    ((0, 1), (5, 10), [(0, 1)]),
    ((5, 10), (0, 1), [(5, 10)]),
])
def test_sector_sub_operation(sector_a, sector_b, expected):
    new_sector = Sector(*sector_a) - Sector(*sector_b)
    assert new_sector == [Sector(*s) for s in expected]


def test_sectors_simple_creation():
    sectors = memory.Sectors([Sector(5, 10), Sector(0, 10)])
    assert sectors._sectors == [Sector(0, 10)]


def test_multiple_sectors_simple_creation():
    sectors = memory.Sectors([Sector(5, 7), Sector(0, 3)])
    assert sectors._sectors == [Sector(0, 3), Sector(5, 7)]


def test_sectors_simple_add():
    sectors = memory.Sectors([Sector(0, 10)])
    new_sectors = sectors + Sector(15, 20)
    assert new_sectors._sectors == [Sector(0, 10), Sector(15, 20)]


def test_sectors_union_add():
    sectors = memory.Sectors([Sector(0, 10), Sector(15, 20)])
    new_sectors = sectors + Sector(5, 15)
    assert new_sectors._sectors == [Sector(0, 20)]


def test_sectors_simple_iadd():
    sectors = memory.Sectors([Sector(0, 10)])
    sectors += Sector(15, 20)
    assert sectors._sectors == [Sector(0, 10), Sector(15, 20)]


@pytest.mark.parametrize("sectors,expected", [
    ([(0, 10), (5, 15)], [(0, 15)]),
    ([(0, 10), (5, 15), (10, 20)], [(0, 20)]),
    ([(0, 10), (5, 15), (18, 30)], [(0, 15), (18, 30)]),
    ([(0, 10), (5, 15), (18, 30)], [(0, 15), (18, 30)]),
    ([(0, 1), (5, 15), (18, 30)], [(0, 1), (5, 15), (18, 30)]),
    ([(0, 20), (5, 10), (6, 7)], [(0, 20)]),
    ([(6, 7), (5, 10), (0, 20)], [(0, 20)]),
])
def test_sectors_adds(sectors, expected):
    sectors = memory.Sectors([Sector(*s) for s in sectors])
    assert sectors._sectors == [Sector(*s) for s in expected]


def test_sectors_simple_sub():
    sectors = memory.Sectors([Sector(0, 10)])
    new_sectors = sectors - Sector(5, 10)
    assert new_sectors._sectors == [Sector(0, 5)]


def test_sectors_splitting_sub():
    sectors = memory.Sectors([Sector(0, 10), Sector(15, 20)])
    new_sectors = sectors - Sector(5, 15)
    assert new_sectors._sectors == [Sector(0, 5), Sector(15, 20)]


def test_sectors_hard_splitting_sub():
    sectors = memory.Sectors([Sector(0, 10), Sector(13, 20)])
    new_sectors = sectors - Sector(5, 15)
    assert new_sectors._sectors == [Sector(0, 5), Sector(15, 20)]


def test_sectors_split_one_sector():
    sectors = memory.Sectors([Sector(0, 10), Sector(13, 20)])
    new_sectors = sectors - Sector(4, 7)
    expected = [Sector(0, 4), Sector(7, 10), Sector(13, 20)]
    assert new_sectors._sectors == expected


def test_sectors_sub_nothing():
    plain_sectors = [
        Sector(0, 10),
        Sector(15, 20),
        Sector(25, 30),
        Sector(26, 31),
        Sector(40, 50),
    ]
    sectors = memory.Sectors(plain_sectors)
    new_sectors = sectors - Sector(2, 5) - Sector(7, 8)
    remains = [Sector(0, 2), Sector(5, 7), Sector(8, 10)]
    assert new_sectors._sectors == remains + plain_sectors[1:]
    new_sectors -= Sector(9, 42)
    remains = [Sector(0, 2), Sector(5, 7), Sector(8, 9)]
    assert new_sectors._sectors == [*remains, Sector(42, 50)]


def test_allow_access_beyond_index():
    mem = Memory(4)
    mem[0] = Dat.of(500)
    assert mem[0] == Dat.of(500)
    assert mem[4] == Dat.of(500)


def test_allow_assignment_beyond_index():
    mem = Memory(4)
    mem[0] = Instruction.from_int(1)
    assert mem[0] == 1
    mem[4] = Instruction.from_int(5)
    assert mem[0] == 5
    assert mem[4] == 5
