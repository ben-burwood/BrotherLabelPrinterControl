from logging import getLogger

from . import ItemType
from ..constants import Resolution
from ..page import BasePage
from ..utils.image import image_to_bitmap

logger = getLogger(__name__)


class Label(BasePage):
    def __init__(self, item: ItemType) -> None:
        self.item = item
        self._bitmap, self._width, self._length = image_to_bitmap(self.item.render())
        self._resolution = Resolution.LOW

        logger.debug(f"label width {self._width}")
        logger.debug(f"label length {self._length}")

        super().__init__()
