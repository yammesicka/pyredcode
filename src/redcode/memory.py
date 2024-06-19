import bisect
from copy import deepcopy
from collections.abc import Iterator
from dataclasses import dataclass
import json
import secrets
from typing import Optional, TypeVar

from redcode.errors import (
    BadMode, RedcodeIndexError, RedcodeOutOfMemoryError, RedcodeRuntimeError
)
from redcode.instruction import Dat, Instruction, Mode


T = TypeVar("T")


@dataclass(frozen=True)
class Sector:
    start: int
    end: int

    def __post_init__(self):
        if self.start < 0 or self.end < 0:
            raise ValueError("Sector bounds must be positive")
        if self.start >= self.end:
            raise ValueError("Sector start must be less than end")

    def to_slice(self) -> slice:
        return slice(self.start, self.end)

    def __len__(self):
        return self.end - self.start

    def __lt__(self, sector: "Sector") -> bool:
        return (self.start, self.end) < (sector.start, sector.end)

    def __leq__(self, sector: "Sector") -> bool:
        return (self.start, self.end) <= (sector.start, sector.end)

    def __eq__(self, sector: object) -> bool:
        if not isinstance(sector, Sector):
            return False
        return self.start == sector.start and self.end == sector.end

    def __contains__(self, sector: "Sector") -> bool:
        return self.start <= sector.start and sector.end <= self.end

    def __and__(self, sector: "Sector") -> Optional["Sector"]:
        start = max(self.start, sector.start)
        end = min(self.end, sector.end)
        if start >= end:
            return None
        return Sector(start, end)

    def __sub__(self, sector: "Sector") -> list["Sector"]:
        if not (self & sector):
            return [self]

        to_return = []
        if sector.start > self.start:
            to_return.append(Sector(self.start, sector.start))
        if sector.end < self.end:
            to_return.append(Sector(sector.end, self.end))

        return to_return

    def __repr__(self):
        start = self.start
        end = self.end
        return (
            f"{self.__class__.__name__}("
            f"{start=!r}, "
            f"{end=!r}"
            ")"
        )


class Sectors:
    def __init__(self, sectors: list[Sector]):
        self._sectors = sectors
        self._sectors.sort(key=lambda s: s.start)
        self.consolidate()

    @staticmethod
    def _add(mem: "Sectors", sector_b: Sector) -> "Sectors":
        index = bisect.bisect_left(mem._sectors, sector_b)
        mem._sectors.insert(index, sector_b)
        mem.consolidate()
        return mem

    @staticmethod
    def _sub(mem: "Sectors", taken: Sector) -> "Sectors":
        sectors = []
        for sector in mem._sectors:
            if taken.start <= sector.end and taken.end >= sector.start:
                if sector.start < taken.start:
                    bisect.insort(sectors, Sector(sector.start, taken.start))
                if sector.end > taken.end:
                    bisect.insort(sectors, Sector(taken.end, sector.end))
            else:
                bisect.insort(sectors, sector)

        mem._sectors = sectors
        mem.consolidate()
        return mem

    def find_block(self, minimum_size: int = 0) -> Iterator[Sector]:
        for sector in self._sectors:
            if len(sector) >= minimum_size:
                yield sector

    def consolidate(self) -> None:
        i = 0
        while i < len(self._sectors) - 1:
            sector = self._sectors[i]
            next_sector = self._sectors[i + 1]
            if sector.end >= next_sector.start:
                max_end = max(sector.end, next_sector.end)
                self._sectors[i] = Sector(sector.start, max_end)
                self._sectors.pop(i + 1)
            else:
                i += 1

    def __len__(self):
        return sum(len(sector) for sector in self._sectors)

    def __eq__(self, sectors: object) -> bool:
        if not isinstance(sectors, Sectors):
            return False
        return self._sectors == sectors._sectors

    def __add__(self, sector: Sector) -> "Sectors":
        mem = deepcopy(self)
        return self._add(mem, sector)

    def __iadd__(self, sector: Sector) -> "Sectors":
        return self._add(self, sector)

    def __sub__(self, sector: Sector) -> "Sectors":
        mem = deepcopy(self)
        return self._sub(mem, sector)

    def __isub__(self, sector: Sector) -> "Sectors":
        return self._sub(self, sector)

    def __iter__(self):
        return iter(self._sectors)


class Memory:
    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("Memory size must be greater than 0")

        self._data: list[int | Instruction] = [Dat.of(0) for _ in range(size)]
        self._free = Sectors([Sector(0, size)])
        self._index = 0

    def allocate(
        self, code: list[Instruction], override: bool = True,
    ) -> int:
        free_sectors = self._get_free_sectors(len(code), override)
        sector = secrets.choice(free_sectors)
        code_start_i = secrets.randbelow(len(sector) - len(code) + 1)
        code_start = code_start_i + sector.start
        code_end = code_start + len(code)
        code_sector = Sector(code_start, code_end)
        self._data[code_sector.to_slice()] = code
        self._free -= code_sector
        return code_sector.start

    def address(self, mode: Mode, value: int, ip: int) -> int:
        if mode == Mode.RELATIVE:
            return (ip + value) % len(self)
        elif mode == Mode.INDIRECT:
            pointer = self.address(Mode.RELATIVE, value, ip)
            address_a = (pointer + int(self[pointer])) % len(self)
            return address_a
        else:
            raise BadMode(f"Unknown mode for address retrieving: {mode}")

    def value(self, mode: Mode, value: int, ip: int) -> int | Instruction:
        if mode == Mode.IMMEDIATE:
            return value
        elif mode == Mode.RELATIVE:
            return self.safely_read_int(self.address(mode, value, ip))
        elif mode == Mode.INDIRECT:
            return self.safely_read_int(self.address(mode, value, ip))
        else:
            raise BadMode(f"Unknown mode for value retrieving: {mode}")

    def _get_free_sectors(self, min_size: int, override: bool) -> list[Sector]:
        if min_size > len(self):
            raise RedcodeOutOfMemoryError(
                f"Allocation passed memory size: {min_size} > {len(self)}"
            )

        if override:
            return [Sector(0, len(self))]

        free_sectors = list(self._free.find_block(minimum_size=min_size))
        if not free_sectors:
            raise RedcodeOutOfMemoryError(
                f"Memory allocation failed for {min_size=} (no free sectors)"
            )
        return free_sectors

    def safely_read_int(self, address: int) -> int:
        return int(self._data[address % len(self)])

    def safely_read_instruction(
        self, address: int | None, default: T = None,
    ) -> Instruction | T:
        if not isinstance(address, int):
            return default

        try:
            return self[address]
        except RedcodeRuntimeError:
            return default

    def as_json(self) -> str:
        return json.dumps([
            str(self.safely_read_instruction(i, "???"))
            for i in range(len(self))
        ])

    def __getitem__(self, address: int) -> Instruction:
        try:
            data = int(self._data[address % len(self)]) % Instruction.SIZE
            return Instruction.from_int(data)  # Might fire RedcodeRuntimeError
        except IndexError:
            raise RedcodeIndexError(f"Address {address} is out of bounds")

    def __setitem__(self, address: int, value: int | Instruction):
        try:
            index = int(address) % len(self)
            self._data[index] = value
        except IndexError:
            raise RedcodeIndexError(f"Address {address} is out of bounds")
        else:
            self._free -= Sector(index, index + 1)

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index >= len(self._data):
            raise StopIteration
        result = self._data[self._index]
        self._index += 1
        return result
