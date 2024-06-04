from src.errors import RedcodeRuntimeError
from src.instruction import Dat, Instruction
from src.memory import Memory


class Process:
    COUNTER = 0

    def __init__(
        self, code_start: int, memory: Memory, alive: bool = True,
        id: int | None = None, parent_id: int | None = None,
    ):
        self._code_start = code_start
        self._ip = code_start  # Instruction pointer - next line to execute
        self._reason = "OK"
        self._alive = alive
        self._memory = memory
        self._id = self.COUNTER if id is None else id
        self._parent_id = parent_id
        self.COUNTER += 1

    @property
    def is_alive(self) -> bool:
        return self._alive

    def tick(self):
        instruction = self._ensure_instruction(self._memory[self._ip])
        if not self._alive:
            return

        try:
            self._ip = instruction.run(self._ip, self._memory)
        except RedcodeRuntimeError as e:
            self._reason = str(e)
            self.die()

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
