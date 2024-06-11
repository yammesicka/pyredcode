from dataclasses import dataclass
from redcode.errors import RedcodeRuntimeError
from redcode.instruction import Dat, Instruction
from redcode.memory import Memory


@dataclass(frozen=True, slots=True)
class Diff:
    pid: int
    ip: int
    index: int | None
    value: str | None


class Process:
    def __init__(
        self, proc_id: int, code_start: int, memory: Memory,
        name: str | None = None, alive: bool = True,
        parent_id: int | None = None,
    ):
        self.name = name or f"Process {proc_id or 'Unnamed'}"
        self._code_start = code_start
        self._ip = code_start  # Instruction pointer - next line to execute
        self._reason = "OK"
        self._alive = alive
        self._memory = memory
        self._id = proc_id
        self._parent_id = parent_id

    @property
    def is_alive(self) -> bool:
        return self._alive

    def tick(self) -> Diff | None:
        instruction = self._ensure_instruction(self._memory[self._ip])
        if not self._alive:
            return

        try:
            self._ip, mem, value = instruction.run(self._ip, self._memory)
        except RedcodeRuntimeError as e:
            self._reason = str(e)
            self.die()
        else:
            value = str(self._memory.safely_read_instruction(mem, "???"))
            return Diff(self._id, self._ip, mem, value)

    def _ensure_instruction(
        self, instruction: int | Instruction,
    ) -> Instruction:
        if isinstance(instruction, Instruction):
            return instruction

        try:
            return Instruction.from_int(instruction)
        except RedcodeRuntimeError as e:
            self._reason = str(e)
            self.die()
            return Dat.of(0)

    def die(self) -> None:
        self._alive = False

    def __str__(self):
        alive = "alive" if self._alive else "dead"
        death_reason = f" {self._reason}" if not self._alive else ""
        return f"Process {alive}{death_reason} at {self._ip}"

    def __repr__(self):
        code_start = self._ip  # We don't care about the rest
        alive = self._alive
        return (
            f"{self.__class__.__name__}("
            f"{code_start=!r}, "
            f"{alive=!r}"
            ")"
        )
