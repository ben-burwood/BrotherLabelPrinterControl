from __future__ import annotations

from enum import Enum
from typing import NamedTuple

class Resolution(Enum):
    LOW = (180, 180)
    HIGH = (180, 320)


class VariousModesSettings(Enum):
    AUTO_CUT = 0b01000000
    MIRROR_PRINTING = 0b10000000


class AdvancedModeSettings(Enum):
    HALF_CUT = 0b00000100
    CHAIN_PRINTING = 0b00001000
    SPECIAL_TAPE = 0b00010000
    HIGH_RESOLUTION = 0b01000000
    BUFFER_CLEARING = 0b10000000


class ErrorCodes(Enum):
    NO_MEDIA = 0x0001
    CUTTER_JAM = 0x0004
    WEAK_BATTERY = 0x0008
    HIGH_VOLTAGE_ADAPTER = 0x0040
    REPLACE_MEDIA = 0x0100
    COVER_OPEN = 0x1000
    OVERHEATING = 0x2000


class MediaType(Enum):
    NO_MEDIA = 0x00
    LAMINATED_TAPE = 0x01
    NON_LAMINATED_TAPE = 0x03
    HEATSHRINK_TUBE_21 = 0x11
    HEATSHRINK_TUBE_31 = 0x17
    INCOMPATIBLE_TAPE = 0xFF


class TapeInfo(NamedTuple):
    width: int
    length: int
    lmargin: int | None
    printarea: int | None
    rmargin: int | None
    media_type: MediaType | None


class Media(Enum):
    UNSUPPORTED_MEDIA = TapeInfo(0, 0, None, None, None, None)
    NO_MEDIA = TapeInfo(0, 0, None, None, None, None)
    W3_5 = TapeInfo(4, 0, 52, 24, 52, MediaType.LAMINATED_TAPE)
    W6 = TapeInfo(6, 0, 48, 32, 48, MediaType.LAMINATED_TAPE)
    W9 = TapeInfo(9, 0, 39, 50, 39, MediaType.LAMINATED_TAPE)
    W12 = TapeInfo(12, 0, 29, 70, 29, MediaType.LAMINATED_TAPE)
    W18 = TapeInfo(18, 0, 8, 112, 8, MediaType.LAMINATED_TAPE)
    W24 = TapeInfo(24, 0, 0, 128, 0, MediaType.LAMINATED_TAPE)

    @classmethod
    def get_media(cls, width: int, media_type: MediaType):
        medias = [media_size for media_size in cls if media_size.value.width == width and media_size.value.media_type == media_type]
        if not medias:
            return cls.UNSUPPORTED_MEDIA
        return medias[0]

    @staticmethod
    def get(name: str) -> "Media":
        for media_type in Media:
            if media_type.name.lower() == name.lower():
                return media_type
        raise ValueError(f"Media not found : {name}")


class StatusCodes(Enum):
    STATUS_REPLY = 0x00
    PRINTING_DONE = 0x01
    ERROR_OCCURRED = 0x02
    EDIT_IF_MODE = 0x03
    TURNED_OFF = 0x04
    NOTIFICATION = 0x05
    PHASE_CHANGE = 0x06


class NotificationCodes(Enum):
    NOT_AVAILABLE = 0x00
    COVER_OPEN = 0x01
    COVER_CLOSED = 0x02


class TapeColor(Enum):
    NO_MEDIA = 0x00
    WHITE = 0x01
    OTHER = 0x02
    CLEAR = 0x03
    RED = 0x04
    BLUE = 0x05
    YELLOW = 0x06
    GREEN = 0x07
    BLACK = 0x08
    CLEAR_WHITE_TEXT = 0x09
    MATTE_WHITE = 0x20
    MATTE_CLEAR = 0x21
    MATTE_SILVER = 0x22
    SATIN_GOLD = 0x23
    SATIN_SILVER = 0x24
    BLUE_D = 0x30
    RED_D = 0x31
    FLUORESCENT_ORANGE = 0x40
    FLUORESCENT_YELLOW = 0x41
    BERRY_PINK_S = 0x50
    LIGHT_GRAY_S = 0x51
    LIME_GREEN_S = 0x52
    YELLOW_F = 0x60
    PINK_F = 0x61
    BLUE_F = 0x62
    WHITE_HEAT_SHRINK_TUBE = 0x70
    WHITE_FLEX_ID = 0x90
    YELLOW_FLEX_ID = 0x91
    CLEANING = 0xF0
    STENCIL = 0xF1
    INCOMPATIBLE = 0xFF


class TextColor(Enum):
    NO_MEDIA = 0x00
    WHITE = 0x01
    OTHER = 0x02
    RED = 0x04
    BLUE = 0x05
    BLACK = 0x08
    GOLD = 0x0A
    BLUE_F = 0x62
    CLEANING = 0xF0
    STENCIL = 0xF1
    INCOMPATIBLE = 0xFF
