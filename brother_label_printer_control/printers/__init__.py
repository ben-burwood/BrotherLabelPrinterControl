import logging
import struct
from abc import ABC, abstractmethod
from logging import getLogger
from typing import TypeVar

import packbits

from .status import Status
from ..backends import BaseBackend, UniDirectionalBackend
from ..constants import AdvancedModeSettings, Media, Resolution, VariousModesSettings
from ..job import Job

logger = getLogger(__name__)

BackendType = TypeVar("BackendType", bound=BaseBackend)


class BasePrinter(ABC):
    """Base class for printers. All printers define this API.  Any other
    methods are prefixed with a _ to indicate they are not part of the
    printer API"""

    def __init__(self, backend: BackendType):
        self._backend = backend

    @abstractmethod
    def print(self, job: Job): ...


def encode_line(bitmap_line: bytes, padding) -> bytes:
    # The number of bits we need to add left or right is not always a multiple
    # of 8, so we need to convert our line into an int, shift it over by the
    # left margin and convert it to back again, padding to 16 bytes.

    # print("".join(f"{x:08b}".replace("0", " ") for x in bytes(bitmap_line)))
    line_int = int.from_bytes(bitmap_line, byteorder="big")
    line_int <<= padding
    padded = line_int.to_bytes(16, byteorder="big")

    # pad to 16 bytes
    compressed = packbits.encode(padded)
    logger.debug("original bitmap: %s", bitmap_line)
    logger.debug("padded bitmap %s", padded)
    logger.debug("packbit compressed %s", compressed)
    # <h: big endian short (2 bytes)
    prefix = struct.pack("<H", len(compressed))

    return prefix + compressed


class GenericPrinter(BasePrinter):
    _SUPPORTED_RESOLUTIONS = (Resolution.LOW, Resolution.HIGH)
    _FEATURE_HALF_CUT = True

    def __init__(self, backend: BackendType):
        super().__init__(backend)

    def reset(self):
        self._backend.write(b"\x00" * 100)  # Invalidate command
        self._backend.write(b"\x1b@")  # Initialize command 1b 40

    def get_status(self) -> Status:
        if hasattr(self._backend, "get_status"):
            data = self._backend.get_status()
        elif isinstance(self._backend, UniDirectionalBackend):
            raise RuntimeError("Backend is unidirectional")
        else:
            self.reset()
            self._backend.write(b"\x1BiS")
            data = self._backend.read(32)
        if not data:
            raise IOError("No Response from printer")

        if len(data) < 32:
            raise IOError("Invalid Response from printer")

        return Status(data)

    def print(self, job: Job, timeout: int = 1000):
        logger.info("starting print")

        self.reset()

        if job.media in (Media.NO_MEDIA, Media.UNSUPPORTED_MEDIA):
            raise RuntimeError("Unsupported Media")

        if job.resolution not in self._SUPPORTED_RESOLUTIONS:
            raise RuntimeError("Resolution is not supported by this printer.")

        media_type = job.media.value.media_type.value.to_bytes(1, "big")
        media_size = job.media.value.width.to_bytes(1, "big")
        offset = job.media.value.lmargin

        various_mode = 0
        if job.auto_cut:
            various_mode = various_mode | VariousModesSettings.AUTO_CUT.value
            auto_cut = True
        else:
            auto_cut = False
        if job.mirror_printing:
            various_mode = various_mode | VariousModesSettings.MIRROR_PRINTING.value
        various_mode = various_mode.to_bytes(1, "big")

        advanced_mode = 0
        if job.half_cut:
            if not self._FEATURE_HALF_CUT:
                raise RuntimeError("Half cut is not supported by this printer.")
            advanced_mode = advanced_mode | AdvancedModeSettings.HALF_CUT.value
        if not job.chain:
            advanced_mode = advanced_mode | AdvancedModeSettings.CHAIN_PRINTING.value
        if job.special_tape:
            advanced_mode = advanced_mode | AdvancedModeSettings.SPECIAL_TAPE.value
        if job.resolution == Resolution.HIGH:
            margin = b"\x1C\x00"
            advanced_mode = advanced_mode | AdvancedModeSettings.HIGH_RESOLUTION.value
        else:
            margin = b"\x0E\x00"
        advanced_mode = advanced_mode.to_bytes(1, "big")

        cut_each = job.cut_each.to_bytes(1, "big")

        for i, page in enumerate(job):
            # switch dynamic command mode: enable raster mode
            self._backend.write(b"\x1Bia\x01")

            # Print information command
            # b'\x1Biz\x86\x01\x0c\x00\x00\x00\00\x00\x00'
            information_command = b"\x1Biz\x86" + media_type + media_size + b"\x00\x00\x00\00\x00\x00"
            self._backend.write(information_command)
            if i == 0 and auto_cut:
                # Ugly workaround
                # Print information command a second time forces cutting after first page.
                # No idea why this is needed, but it works
                self._backend.write(information_command)

            # Various mode
            logger.debug(f"various_mode: {various_mode}")
            self._backend.write(b"\x1BiM" + various_mode)

            # Advanced mode
            logger.debug(f"advanced_mode: {advanced_mode}")
            self._backend.write(b"\x1biK" + advanced_mode)

            # margin
            self._backend.write(b"\x1bid" + margin)

            if auto_cut:
                # Configure after how many pages a cut should be done
                self._backend.write(b"\x1BiA" + cut_each)

            # Enable compression mode
            self._backend.write(b"M\x02")

            # send rastered lines
            for line in page:
                logging.debug(f"line: {line}")
                self._backend.write(b"G" + encode_line(line, offset), timeout=timeout)

            self._backend.write(b"Z")

            logging.debug(f"i: {i}")
            if i < len(job) - 1:
                self._backend.write(b"\x0C")

        # end page
        self._backend.write(b"\x1A")
        logger.info("end of page")
