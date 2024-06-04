from pathlib import Path

from src import config
from src.instruction import Instruction
from src.code import Parser, Validator
from src.memory import Memory
from src.process import Process


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

    def _spawn_process(self, program: list[Instruction]) -> None:
        code_start = self.memory.allocate(program, override=False)
        self.processes.append(Process(code_start, self.memory))

    def _create_code_from_text(self, code: str) -> list[Instruction]:
        validator = Validator(code)
        if not validator.is_valid():
            raise ExceptionGroup("Code parsing failed", validator.errors)

        program = Parser(code)
        return program.instructions

    def load_file(self, path: str | Path) -> None:
        path = Path(path)
        text = path.read_text()
        code = self._create_code_from_text(text)
        self._spawn_process(code)

    def run(self):
        for process in self.processes:
            process.tick()
