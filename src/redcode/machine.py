import copy
import dataclasses
import json
from pathlib import Path

from redcode import config
from redcode.code import Parser, Validator
from redcode.errors import MachineAlreadyRunning
from redcode.instruction import Instruction
from redcode.memory import Memory
from redcode.process import Diff, Process


class Machine:
    def __init__(
        self,
        memory_size: int = config.MEMORY_SIZE,
        allow_single_process: bool = False,
    ):
        self.memory = Memory(memory_size)
        self.processes: list[Process] = []
        self.start_state: Machine | None = None
        self.start_map: list[int | None] = [None] * len(self.memory)
        self._history: list[Diff | None] = []
        self._ticks = 0
        self._allow_single_process = allow_single_process

    def __getitem__(self, address: int) -> int | Instruction:
        return self.memory[address]

    def __setitem__(self, address: int, value: Instruction) -> None:
        self.memory[address] = value

    def reset(self):
        self.memory = Memory(len(self.memory))
        self.processes.clear()
        self.start_state = None
        self._history.clear()
        self._ticks = 0

    def _spawn_process(
        self, program: list[Instruction], player_name: str,
    ) -> None:
        code_starts = self.memory.allocate(program, override=False)
        code_ends = code_starts + len(program)
        process = Process(code_starts, self.memory, player_name)
        self.start_map[code_starts:code_ends] = [process._id] * len(program)
        self.processes.append(process)

    def _create_code_from_text(self, code: str) -> list[Instruction]:
        validator = Validator(code)
        if not validator.is_valid():
            raise ExceptionGroup("Code parsing failed", validator.errors)

        program = Parser(code)
        program.parse()
        return program.instructions

    @property
    def _processes_alive(self) -> int:
        return sum(process.is_alive for process in self.processes)

    @property
    def halted(self) -> bool:
        if self._allow_single_process and self._processes_alive >= 1:
            return False

        return self._processes_alive < 2

    def load_code(self, code: str, player_name: str) -> None:
        program = self._create_code_from_text(code)
        self._spawn_process(program, player_name)

    def load_file(self, path: str | Path, player_name: str) -> None:
        path = Path(path)
        text = path.read_text()
        self.load_code(text, player_name)

    @property
    def history(self) -> list[Diff | None]:
        return self._history

    @property
    def json_history(self) -> str:
        return json.dumps(
            [act and dataclasses.asdict(act) for act in self._history]
        )

    def round(self):
        if self.halted:
            return

        for process in self.processes:
            self._history.append(process.tick())
            self._ticks += 1

    def run(self, max_ticks: int = config.MAX_TICKS):
        if self._ticks > 0:
            raise MachineAlreadyRunning()
        if self.start_state is None:
            self.start_state = copy.deepcopy(self)

        while self._ticks <= max_ticks and not self.halted:
            self.round()
