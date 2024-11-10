from __future__ import annotations

from PIL import Image

from . import Item, ItemType

class Box(Item):
    def __init__(self, height: int, *items: ItemType, vertical: bool = False, left_padding: int = 0) -> None:
        self.height = height
        self.items = items
        self._vertical = vertical
        self._left_padding = left_padding

    def render(self) -> Image:
        rendered_images = [item.render() for item in self.items]
        if self._vertical:
            length = max([rendered_image.size[0] for rendered_image in rendered_images]) + self._left_padding
            assert self.height == sum([rendered_image.size[1] for rendered_image in rendered_images])
            image = Image.new("1", (length, self.height), "white")
            xpos = 0
            for rendered_image in rendered_images:
                image.paste(rendered_image, (self._left_padding, xpos))
                xpos += rendered_image.size[1]
        else:
            length = sum([rendered_image.size[0] for rendered_image in rendered_images]) + self._left_padding
            image = Image.new("1", (length, self.height), "white")
            ypos = self._left_padding
            for rendered_image in rendered_images:
                image.paste(rendered_image, (ypos, 0))
                ypos += rendered_image.size[0]
        return image
