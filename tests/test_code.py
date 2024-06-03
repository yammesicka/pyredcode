from pathlib import Path

import pytest

from src.config import MAX_PROGRAM_SIZE
from src.code import Parser, Validator
from src.errors import SizeLimitExceeded
from src.instruction import Add, Mode, Mov, Jmp


code_dir = Path(__file__).parent / "codes"


def test_inparsable_codes():
    for codefile in code_dir.glob("bad_*.red"):
        code = codefile.read_text()
        assert not Validator(code).is_valid()


def test_parsable_codes():
    codes = list(code_dir.glob("*.red"))
    good_codes = [c for c in codes if not c.name.startswith("bad")]
    for codefile in good_codes:
        code = codefile.read_text()
        run = Validator(code)
        assert run.is_valid(), (codefile, run.errors)


def test_validator_right_lines():
    code = (code_dir / "bad_line_check.red").read_text()
    run = Validator(code)
    assert not run.is_valid()
    assert len(run.errors) == 2
    assert run.errors[0].line_index == 11
    assert run.errors[1].line_index == 16


def test_bad_operand_modifier():
    code = "ADD ~1 2"
    run = Validator(code)
    assert not run.is_valid(), "Tilda shouldn't be a valid modifier"
    assert len(run.errors) == 1
    assert run.errors[0].line_index == 1


def test_parsed_mov():
    code = "MOV #1 0"
    parser = Parser(code)
    parser.parse()
    assert parser.instructions == [Mov(Mode.IMMEDIATE, 1, Mode.RELATIVE, 0)]


def test_parsed_jmp():
    code = "JMP 1"
    parser = Parser(code)
    parser.parse()
    assert parser.instructions == [Jmp(Mode.RELATIVE, 1)]


def test_parser_classic():
    code = (code_dir / "good.red").read_text()
    parser = Parser(code)
    parser.parse()
    assert parser.instructions == [
        Add(Mode.IMMEDIATE, 4, Mode.RELATIVE, -1),
        Mov(Mode.IMMEDIATE, 0, Mode.INDIRECT, -2),
        Jmp(Mode.RELATIVE, -2),
        Add(Mode.IMMEDIATE, 4, Mode.RELATIVE, -1),
        Mov(Mode.IMMEDIATE, 0, Mode.INDIRECT, -2),
        Jmp(Mode.RELATIVE, -2),
        Add(Mode.IMMEDIATE, 4, Mode.RELATIVE, -1),
        Mov(Mode.IMMEDIATE, 0, Mode.INDIRECT, -2),
        Jmp(Mode.RELATIVE, -2),
        Add(Mode.IMMEDIATE, 4, Mode.RELATIVE, -1),
        Mov(Mode.IMMEDIATE, 0, Mode.INDIRECT, -2),
    ]


def test_legit_size():
    try:
        code = "MOV #1 0\n\n" * MAX_PROGRAM_SIZE
        Parser(code).parse()
    except Exception:
        assert False, "Code should be valid"


def test_exceeded_size():
    with pytest.raises(SizeLimitExceeded):
        code = "MOV #1 0\n\n" * (MAX_PROGRAM_SIZE + 1)
        Parser(code).parse()


def test_disabled_size_limit():
    try:
        code = "MOV #1 0\n\n" * (MAX_PROGRAM_SIZE + 1)
        Parser(code, instruction_limit=None).parse()
    except Exception:
        assert False, "Code should be valid"
