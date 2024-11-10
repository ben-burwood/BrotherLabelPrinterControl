from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from PIL import Image

class Item(ABC):
    @abstractmethod
    def render(self) -> Image: ...


ItemType = TypeVar("ItemType", bound=Item)
