from __future__ import annotations

from abc import ABC
from math import ceil
from typing import TypeVar

from PIL import Image

from .constants import Resolution
from .utils.image import bitmap_to_image, image_to_bitmap


class BasePage(ABC):
    _bitmap: bytes
    _width: int
    _length: int
    _resolution: Resolution

    def __init__(self):
        self.__byte_per_line = None
        self.__image = None
        assert self._byte_per_line * self.length == len(self.bitmap)

    @property
    def bitmap(self) -> bytes:
        return self._bitmap

    @property
    def width(self):
        return self._width

    @property
    def length(self):
        return self._length

    @property
    def resolution(self):
        return self._resolution

    @property
    def _byte_per_line(self):
        if self.__byte_per_line is None:
            self.__byte_per_line = ceil(self.width / 8)
        return self.__byte_per_line

    def __iter__(self):
        for i in range(0, len(self.bitmap), self._byte_per_line):
            yield self.bitmap[i : i + self._byte_per_line]

    @property
    def image(self) -> Image:
        if not self.__image:
            self.__image = bitmap_to_image(self._bitmap, self._width, self.length)
        return self.__image


PageType = TypeVar("PageType", bound=BasePage)


class Page(BasePage):
    def __init__(self, bitmap: bytes, width: int, length: int, resolution: Resolution = Resolution.LOW):
        self._bitmap = bitmap
        self._width = width
        self._length = length
        self._resolution = resolution
        super().__init__()

    @classmethod
    def from_image(cls, image: Image, resolution: Resolution = Resolution.LOW) -> Page:
        bitmap, width, length = image_to_bitmap(image)
        return cls(bitmap, width, length, resolution)
