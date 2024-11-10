from __future__ import annotations

from typing import Optional

from PIL import Image

from . import Item

try:
    from qrcode import QRCode as _QRCode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_H, ERROR_CORRECT_Q
except ImportError:
    _QRCode = None
    ERROR_CORRECT_L = 1
    ERROR_CORRECT_M = 0
    ERROR_CORRECT_Q = 3
    ERROR_CORRECT_H = 2


class QRCode(Item):
    def __init__(self, width: int, data: str, error_correction: Optional[ERROR_CORRECT_M | ERROR_CORRECT_H | ERROR_CORRECT_Q] = None, box_size: int | None = None, border: int = 0) -> None:
        if _QRCode is None:
            raise RuntimeError("No QR code support. Package qrcode is not installed.")
        self._width = width
        self._data = data
        self._error_correction = error_correction
        self._box_size = box_size
        self._border = border

    def render(self) -> Image:
        if self._box_size is None:
            box_size = 2
        else:
            box_size = self._box_size
        probe_box_size = box_size
        qr_image = None
        if self._error_correction is None:
            error_corrections = [ERROR_CORRECT_H, ERROR_CORRECT_Q, ERROR_CORRECT_M, ERROR_CORRECT_L]
        else:
            error_corrections = [self._error_correction]
        error_correction = None
        for error_correction in error_corrections:
            while True:
                logger.debug(f"qrcode: {self._data}, probe_box_size: {probe_box_size}, EC: {error_correction}")
                qr = _QRCode(error_correction=error_correction, box_size=probe_box_size, border=self._border)
                qr.add_data(self._data)
                new_image = qr.make_image()
                if new_image.size[0] <= self._width:
                    qr_image = new_image
                    probe_box_size += 1
                elif qr_image is None:
                    break
                else:
                    break
                if self._box_size is not None:
                    break
            if qr_image:
                break
        if not qr_image:
            raise RuntimeError("Data does not fit in qrcode")

        logger.debug(f"qrcode: {self._data}, final box_size: {probe_box_size - 1}, EC: {error_correction}")

        rest = self._width - qr_image.size[1]
        image = Image.new("1", (qr_image.size[0], self._width), "white")
        image.paste(qr_image, (0, rest // 2))

        return image
