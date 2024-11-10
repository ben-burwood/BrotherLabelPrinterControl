from enum import Enum, auto
from typing import Type

from . import BaseBackend
from .bluetooth import BTSerialBackend
from .network import NetworkBackend
from .usb import PyUSBBackend


class Backend(Enum):
    USB = auto()
    WIFI = auto()
    BLUETOOTH = auto()

    @property
    def backend(self) -> Type[BaseBackend]:
        match self:
            case Backend.USB:
                return PyUSBBackend
            case Backend.BLUETOOTH:
                return BTSerialBackend
            case Backend.WIFI:
                return NetworkBackend

    @staticmethod
    def get(name: str) -> "Backend":
        for connection_type in Backend:
            if connection_type.name.lower() == name.lower():
                return connection_type
        raise ValueError(f"Backend with name {name} not found")
