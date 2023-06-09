import json
from abc import ABC, abstractproperty
from pathlib import Path
from typing import Generic, Self, TypedDict, TypeVar

import aiofiles

from .errors import InvalidSaveLocation

D = TypeVar('D', bound=TypedDict)


class SaveableAsJSON(ABC, Generic[D]):
    data: D
    _save_location: Path | None

    def __init__(self, save_location: Path | None = None) -> None:
        self.location = save_location

    @property
    def location(self) -> Path:
        if self._save_location is None:
            raise InvalidSaveLocation('Save location is None but must be a Path object.')

        return self._save_location

    @location.setter
    def location(self, new_location: Path | None) -> None:
        if new_location is not None and new_location.exists() and not new_location.is_file():
            raise InvalidSaveLocation(f'Save location must be a file, not {new_location.stat().st_mode}')

        self._save_location = new_location

    async def save(self, new_location: Path) -> None:
        if new_location is None:
            assert self.location is not None
            new_location = self.location

        async with aiofiles.open(new_location, 'w') as file:
            await file.write(json.dumps(self.data))

        self.location = new_location

    async def load(self, save_location: Path) -> None:
        if not save_location.exists() or not save_location.is_file():
            raise InvalidSaveLocation(f'Save location must be a file, not {save_location.stat().st_mode}')

        async with aiofiles.open(save_location, 'r') as file:
            content: str = '\n'.join(await file.readlines())
            new_data: D = json.loads(content)

        self.data = new_data

    async def __aenter__(self) -> Self:
        await self.load(self.location)
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb) -> None:
        await self.save(self.location)
