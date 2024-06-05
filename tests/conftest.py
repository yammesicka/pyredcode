import pytest

from redcode.instruction import Add, Jmp, Mode, Mov


@pytest.fixture
def code():
    return [
        Add(Mode.IMMEDIATE, 4, Mode.RELATIVE, -1),
        Mov(Mode.IMMEDIATE, 0, Mode.INDIRECT, -2),
        Jmp(Mode.RELATIVE, -2),
    ]
