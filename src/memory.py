from collections.abc import Iterator
from dataclasses import dataclass
from typing import TypeAlias
import secrets

from src.errors import RedcodeIndexError, RedcodeRuntimeError
from src.instruction import Dat, Instruction


CellType: TypeAlias = int


class Mode:
    IMMEDIATE = 0
    RELATIVE = 1
    INDIRECT = 2


@dataclass(frozen=True)
class Sector:
    start: int
    end: int

    def __len__(self):
        return self.end - self.start


class Memory:
    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("Memory size must be greater than 0")

        self._data: list[Instruction] = [Dat.of(0) for _ in range(size)]
        self._free_sections = [Sector(0, size)]
        self._index = 0

    def _get_fitting_sectors(self, code_size: int) -> Iterator[int]:
        for i, sector in enumerate(self._free_sections):
            if sector.end - sector.start >= code_size:
                yield i

    def allocate(self, code: list[Instruction]) -> None:
        free_sectors = list(self._get_fitting_sectors(code_size=len(code)))
        if not free_sectors:
            raise RedcodeRuntimeError(f"Can't allocate memory for {code=}")
        sector_index = secrets.choice(free_sectors)
        sector_size = len(self._free_sections[sector_index])

        code_allocation_start = secrets.randbelow(sector_size - len(code) + 1)
        code_allocation_end = code_allocation_start + len(code)
        self._data[code_allocation_start:code_allocation_end] = code

        self._split_sector(sector_index, code_allocation_start, len(code))

    def _split_sector(
        self, sector_index: int, allocation_start_index: int, code_size: int,
    ) -> None:
        sector = self._free_sections.pop(sector_index)
        start, end = sector.start, sector.end
        code_start = start + allocation_start_index
        add_sector = self._free_sections.insert
        if start < code_start:
            add_sector(sector_index, Sector(start, code_start))
        if code_start + code_size < end:
            add_sector(sector_index + 1, Sector(code_start + code_size, end))

    def __getitem__(self, address: int) -> Instruction:
        try:
            return self._data[address]
        except IndexError:
            raise RedcodeIndexError(f"Address {address} is out of bounds")

    def __setitem__(self, address: int, value: Instruction):
        try:
            self._data[address] = value
        except IndexError:
            raise RedcodeIndexError(f"Address {address} is out of bounds")

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self._data):
            result = self._data[self._index]
            self._index += 1
            return result
        else:
            raise StopIteration
