from __future__ import annotations

from logging import getLogger
from math import ceil
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont

from . import Item
from ..utils.image import crop

logger = getLogger(__name__)


class Padding(NamedTuple):
    left: int
    top: int
    bottom: int
    right: int

    @staticmethod
    def from_dict(data: dict) -> Padding:
        return Padding(data.get("left", 0), data.get("top", 0), data.get("bottom", 0), data.get("right", 0))


class Text(Item):
    def __init__(self, height: int, text: str, font_path: str, font_index: int = 0, font_size: int | None = None, padding: Padding = Padding(0, 0, 0, 0)) -> None:
        self.text = text
        self.height = height
        self.font_path = font_path
        self.font_index = font_index
        self.font_size = font_size

        if any([i < 0 for i in padding]):
            raise ValueError("Negative padding is not supported: {padding}")
        self.padding = padding

    def render(self) -> Image:
        iheight = self.height - self.padding.top - self.padding.bottom
        if self.font_size is None:
            font_size = self._calc_font_size(iheight)
            logger.debug(f"text: {self.text}, calculated font size: {font_size}")
        else:
            font_size = self.font_size
        font = ImageFont.truetype(self.font_path, font_size, self.font_index)
        text_x, _ = font.getsize(self.text)
        image = Image.new("1", (self.padding.left + text_x + self.padding.right, self.height), "white")
        fimage = Image.new("1", font.getsize(self.text), "white")
        draw = ImageDraw.Draw(fimage)
        draw.text((0, 0), self.text, "black", font)
        fimage = crop(fimage)
        image.paste(fimage, (self.padding.left, self.padding.top))
        return image

    def _calc_font_size(self, height: int) -> int:
        lower = 1
        upper = 1
        while True:
            font = ImageFont.truetype(self.font_path, upper)
            image = Image.new("1", font.getsize(self.text), "white")
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), self.text, "black", font)
            font_height = crop(image).size[1]
            if font_height >= height:
                break
            lower = upper
            upper *= 2
        while True:
            test = ceil((upper + lower) / 2)
            font = ImageFont.truetype(self.font_path, test)
            image = Image.new("1", font.getsize(self.text), "white")
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), self.text, "black", font)
            font_height = crop(image).size[1]
            if upper - lower <= 1:
                return lower
            elif font_height > height:
                upper = test
            elif font_height < height:
                lower = test
            else:
                return test
