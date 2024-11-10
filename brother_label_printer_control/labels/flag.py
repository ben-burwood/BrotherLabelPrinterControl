from logging import getLogger

from PIL.Image import Image

from .label import ItemType
from ..constants import Resolution
from ..page import BasePage
from ..utils.image import bitmap_to_image, image_to_bitmap

logger = getLogger(__name__)


class Flag(BasePage):
    def __init__(self, item1: ItemType, item2: ItemType, spacing=265) -> None:
        rendered_images = [item1.render(), item2.render()]
        image_max_length = max([rendered_image.size[0] for rendered_image in rendered_images])
        length = 2 * image_max_length + spacing
        height = max([rendered_image.size[1] for rendered_image in rendered_images])

        line_length = 2 + spacing % 2
        data = 0x0
        for i in range(height - 1):
            data <<= 1
            if not i % 8:
                data |= 0x01
        b_len = round(height / 8)
        data <<= b_len * 8 - height
        bitmap = line_length * data.to_bytes(b_len, byteorder="big")
        line_image = bitmap_to_image(bitmap, height, line_length)

        white_spacing = (spacing - line_length) // 2

        # spacing_image = Image.new("1", ((spacing - line_length) // 2, height), "white")
        rendered_images.insert(1, line_image)
        positions = [0, image_max_length + white_spacing, line_length + white_spacing]

        image = Image.new("1", (length, height), "white")
        ypos = 0
        for rendered_image, position in zip(rendered_images, positions):
            ypos += position
            image.paste(rendered_image, (ypos, 0))
        self._bitmap, self._width, self._length = image_to_bitmap(image)
        self._resolution = Resolution.LOW

        logger.debug(f"flag width {self._width}")
        logger.debug(f"flag length {self._length}")

        super().__init__()
