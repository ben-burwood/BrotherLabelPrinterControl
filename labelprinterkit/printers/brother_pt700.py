"""
Brother P-Touch P700 Driver
"""
from abc import ABC, abstractmethod
import struct
from collections import namedtuple
from enum import Enum, IntEnum
from itertools import islice
from typing import Iterable, Sequence, Tuple
from math import ceil
import logging

import packbits
from PIL import Image, ImageChops

from ..label import Label
from ..backends import BaseBackend

logger = logging.getLogger(__name__)


class BaseErrorStatus(ABC):
    """Represents the errors the printer has"""
    @abstractmethod
    def any(self):
        """return if any errors have occurred"""
        return any(self.data.values())

    def __getattr__(self, attr):
        return self.data[attr]

    def __repr__(self):
        return "<Errors {}>".format(self.data)


class BaseStatus(ABC):
    """Represents the status of the printer"""
    errors = None  # type: BaseErrorStatus

    def __repr__(self):
        return "<Status {} {} {}>".format(self.data, self.errors,
                                          self.tape_info)

    @abstractmethod
    def __getattr__(self, attr):
        pass

    @abstractmethod
    def ready(self) -> bool:
        """return if the printer is ready for printing"""
        pass


class BasePrinter(ABC):
    """Base class for printers. All printers define this API.  Any other
    methods are prefixed with a _ to indicate they are not part of the
    printer API"""

    DPI = None  # type: Tuple[float, float]

    def __init__(self, backend: BaseBackend) -> None:
        self.backend = backend

    def estimate_label_size(self, label: Label) -> Tuple[float, float]:
        """estimate the Labels size in mm"""

        xdpi, ydpi = self.DPI
        xpixels, ypixels = label.size
        return (xpixels / xdpi) * 2.54, (ypixels / ydpi) * 2.54

    def print_label(self, label: Label) -> BaseStatus:
        """Print the label"""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the Printer"""
        pass


def batch_iter_bytes(b, size):
    i = iter(b)

    return iter(lambda: bytes(tuple(islice(i, size))), b"")


class INFO_OFFSETS(IntEnum):
    PRINTHEAD_MARK = 0
    MODEL_CODE = 4
    ERROR_1 = 8
    ERROR_2 = 9
    MEDIA_WIDTH = 10
    MEDIA_TYPE = 11
    MODE = 15
    MEDIA_LENGTH = 17
    STATUS_TYPE = 18
    PHASE_TYPE = 19
    PHASE_NUMBER_HI = 20
    PHASE_NUMBER_LO = 21
    NOTIFY_NO = 22
    HARDWARE_SETTINGS = 26


class ERRORS(Enum):
    NO_MEDIA = 0
    CUTTER_JAM = 2
    WEAK_BATTERY = 3
    HV_ADAPTER = 6
    REPLACE_MEDIA = 8
    COVER_OPEN = 12
    OVERHEATING = 13
    UNKNOWN = -1


class MEDIA_TYPE(Enum):
    NO_MEDIA = 0
    LAMINATED_TAPE = 1
    NON_LAMINATED_TAPE = 2
    HEAT_SHRINK = 3
    INCOMPATIBLE = 4


class STATUS_TYPE(Enum):
    STATUS_REPLY = 0
    PRINTING_DONE = 1
    ERROR_OCCURRED = 2
    TURNED_OFF = 3
    NOTIFICATION = 4
    PHASE_CHANGE = 5


STATUS_TYPE_MAP = {
    0x00: STATUS_TYPE.STATUS_REPLY,
    0x01: STATUS_TYPE.PRINTING_DONE,
    0x02: STATUS_TYPE.ERROR_OCCURRED,
    0x04: STATUS_TYPE.TURNED_OFF,
    0x05: STATUS_TYPE.NOTIFICATION,
    0x06: STATUS_TYPE.PHASE_CHANGE,
}

MEDIA_TYPE_MAP = {
    0x00: MEDIA_TYPE.NO_MEDIA,
    0x01: MEDIA_TYPE.LAMINATED_TAPE,
    0x02: MEDIA_TYPE.NON_LAMINATED_TAPE,
    0x11: MEDIA_TYPE.HEAT_SHRINK,
    0xFF: MEDIA_TYPE.INCOMPATIBLE,
}

TapeInfo = namedtuple("TapeInfo", ["lmargin", "printarea", "rmargin", "width"])

MEDIA_WIDTH_INFO = {
    # media ID to tape width in dots
    0: TapeInfo(None, None, None, None),
    4: TapeInfo(52, 24, 52, 3.5),
    6: TapeInfo(48, 32, 48, 6.0),
    9: TapeInfo(39, 50, 39, 9.0),
    12: TapeInfo(29, 70, 29, 12.0),
    18: TapeInfo(8, 112, 8, 18.0),
    24: TapeInfo(0, 128, 0, 24.0),
}

ERROR_MASK = {
    0: ERRORS.NO_MEDIA,
    2: ERRORS.CUTTER_JAM,
    3: ERRORS.WEAK_BATTERY,
    6: ERRORS.HV_ADAPTER,
    8: ERRORS.REPLACE_MEDIA,
    12: ERRORS.COVER_OPEN,
    13: ERRORS.OVERHEATING,
}


def encode_line(bitmap_line: bytes, tape_info: TapeInfo) -> bytes:
    # The number of bits we need to add left or right is not always a multiple
    # of 8, so we need to convert our line into an int, shift it over by the
    # left margin and convert it to back again, padding to 16 bytes.

    # print("".join(f"{x:08b}".replace("0", " ") for x in bytes(bitmap_line)))
    line_int = int.from_bytes(bitmap_line, byteorder='big')
    line_int <<= tape_info.rmargin
    padded = line_int.to_bytes(16, byteorder='big')

    # pad to 16 bytes
    compressed = packbits.encode(padded)
    logger.debug("original bitmap: %s", bitmap_line)
    logger.debug("padded bitmap %s", padded)
    logger.debug("packbi compressed %s", compressed)
    # <h: big endian short (2 bytes)
    prefix = struct.pack("<H", len(compressed))

    return prefix + compressed


class Errors(BaseErrorStatus):
    def __init__(self, byte1: int, byte2: int) -> None:
        value = byte1 | (byte2 << 8)
        self.data = {
            err.name.lower(): bool(value & 1 << offset)

            for offset, err in ERROR_MASK.items()
        }

    def any(self):
        return any(self.data.values())

    def __getattr__(self, attr):
        return self.data[attr]

    def __repr__(self):
        return "<Errors {}>".format(self.data)


class Status(BaseStatus):
    def __init__(self, msg: Sequence) -> None:
        self.data = {i.name.lower(): msg[i.value] for i in INFO_OFFSETS}

        self.errors = Errors(self.error_1, self.error_2)
        self.tape_info = MEDIA_WIDTH_INFO[self.media_width]

    def ready(self):
        return not self.errors.any()

    def __getattr__(self, attr):
        return self.data[attr]


class P700(BasePrinter):
    """Printer Class for the Brother P-Touch P700/PT-700 Printer

    Theoretically supports the H500 and E500 too, but this is untested"""
    DPI = (180, 180)

    def connect(self) -> None:
        """Connect to Printer"""
        logger.info("connected")

    def reset(self) -> None:
        self.backend.write(b'\x00' * 100) # Invalidate command
        self.backend.write(b'\x1b@') # Initialize command 1b 40

    def get_status(self) -> Status:
        """get status of the printer as ``Status`` object"""
        self.reset()
        self.backend.write(b'\x1BiS')
        data = self.backend.read(32)
        if not data:
            raise IOError("No Response from printer")

        if len(data) < 32:
            raise IOError("Invalid Response from printer")

        return Status(data)

    def _debug_status(self):
        data = self.backend.read(32)

        if data:
            logger.debug(Status(data))

    def get_label_width(self):
        return self.get_status().tape_info.width

    def print_label(self, label: Label) -> Status:
        status = self.get_status()
        if not status.ready():
            raise IOError("Printer is not ready")

        img = label.render(height=status.tape_info.printarea)
        logger.debug("printarea is %s dots", status.tape_info.printarea)
        if not img.mode == "1":
            raise ValueError("render output has invalid mode '1'")
        img = img.transpose(Image.ROTATE_270).transpose(
            Image.FLIP_TOP_BOTTOM)
        img = ImageChops.invert(img)

        logger.info("label output size: %s", img.size)
        logger.info("tape info: %s", status.tape_info)

        # img.show()
        self._raw_print(
             status, list(batch_iter_bytes(img.tobytes(), ceil(img.size[0] / 8))))
        #return self.get_status()

    def _dummy_print(self, status: Status, document: Iterable[bytes]) -> None:
        for line in document:
            # print(b'G' + encode_line(line, status.tape_info))
            encode_line(line, status.tape_info)

    def _raw_print(self, status: Status, document: Iterable[bytes], count: int = 1) -> None:
        logger.info("starting print")

        self.reset()

        for i in range(0, count):
            # raster mode
            self.backend.write(b'\x1Bia\x01') # switch dynamic command mode 1B 69 61 01
            self._debug_status()

            # Print information command
            self.backend.write(b'\x1Biz\x86\x01\x0c\x00\x00\x00\00\x00\x00')
            #self.backend.write(b'\x1Biz\x84\x00\x0c\x00\x96\x00\00\x00\x00')
            #self._debug_status()

            if i == 0:
                # Ugly workaround
                # Print information command a second time forces cutting after first page.
                # Noe one knows why this is needed
                self.backend.write(b'\x1Biz\x86\x01\x0c\x00\x00\x00\00\x00\x00') # 1B 69 7a ... 84 00 18 00 AA 02 00 00 00 00

            # Various mode
            self.backend.write(b'\x1biM\x40')  # autocut 1B 69 4D 40
            self._debug_status()

            # cut
            #self.backend.write(b'\x1biA' + count.to_bytes(1))
            self.backend.write(b'\x1biA\x01') #1B 69 41 01

            # Advanced mode
            self.backend.write(b'\x1biK\x08') # 1B 69 4B 41 08
            #self.backend.write(b'\x1biK\x00') # 1B 69 4B 41 00
            self._debug_status()

            # margin
            self.backend.write(b'\x1bid\x0E\x00') # 1B 69 64 OE OO
            self._debug_status()

            # Compression mode
            self.backend.write(b'M\x02') # 4d 02
            self._debug_status()

            # raster line
            for line in document:
                self.backend.write(b'G' + encode_line(line, status.tape_info))

            self.backend.write(b'Z')

            if i < count - 1:
                self.backend.write(b'\x0C')

        # end page
        self._debug_status()
        self.backend.write(b'\x1A')
        self._debug_status()
        logger.info("end of page")
