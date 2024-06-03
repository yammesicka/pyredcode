import config

from src.instruction import Instruction
from src.memory import Memory


class Machine:
    def __init__(self, memory_size: int = config.MEMORY_SIZE):
        self.memory = Memory(memory_size)

    def __getitem__(self, address: int) -> Instruction:
        return self.memory[address]

    def __setitem__(self, address: int, value: Instruction) -> None:
        self.memory[address] = value

    def __len__(self):
        return len(self.memory)

    def allocate(self, program: list[Instruction]) -> None:
        self.memory.allocate(program)
