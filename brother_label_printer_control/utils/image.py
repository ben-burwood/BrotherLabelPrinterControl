from __future__ import annotations

from typing import Tuple

from PIL import Image, ImageChops

def image_to_bitmap(image: Image) -> Tuple[bytes, int, int]:
    assert image.mode == "1"
    image = image.transpose(Image.ROTATE_270).transpose(Image.FLIP_TOP_BOTTOM)
    image = ImageChops.invert(image)
    return image.tobytes(), image.size[0], image.size[1]


def bitmap_to_image(bitmap: bytes, width: int, length: int) -> Image:
    image = Image.frombytes("1", (width, length), bitmap)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    image = image.transpose(Image.ROTATE_90)
    image = ImageChops.invert(image)
    return image


def crop(im: Image) -> Image:
    """Crop an image to the non-white area"""
    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        return im.crop(bbox)
    else:
        return im
