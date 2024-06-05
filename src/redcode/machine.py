from pathlib import Path

from redcode import config
from redcode.instruction import Instruction
from redcode.code import Parser, Validator
from redcode.memory import Memory
from redcode.process import Process


class Machine:
    def __init__(self, memory_size: int = config.MEMORY_SIZE):
        self.memory = Memory(memory_size)
        self.processes: list[Process] = []

    def __getitem__(self, address: int) -> int | Instruction:
        return self.memory[address]

    def __setitem__(self, address: int, value: Instruction) -> None:
        self.memory[address] = value

    def __len__(self):
        return len(self.memory)

    def _spawn_process(
        self, program: list[Instruction], player_name: str,
    ) -> None:
        code_start = self.memory.allocate(program, override=False)
        self.processes.append(Process(code_start, self.memory, player_name))

    def _create_code_from_text(self, code: str) -> list[Instruction]:
        validator = Validator(code)
        if not validator.is_valid():
            raise ExceptionGroup("Code parsing failed", validator.errors)

        program = Parser(code)
        program.parse()
        return program.instructions

    def load_code(self, code: str, player_name: str) -> None:
        program = self._create_code_from_text(code)
        self._spawn_process(program, player_name)

    def load_file(self, path: str | Path, player_name: str) -> None:
        path = Path(path)
        text = path.read_text()
        self.load_code(text, player_name)

    def turn(self):
        for process in self.processes:
            process.tick()
