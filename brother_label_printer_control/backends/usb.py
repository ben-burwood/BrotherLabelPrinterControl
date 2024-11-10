from __future__ import annotations

from time import sleep

import usb.core
import usb.util

from .. import BrotherPrinterError
from . import BaseBackend


class PyUSBBackend(BaseBackend):
    """Assumes only a SINGLE USB Printer / Brother Device is Attached"""

    def __init__(self, vendor_id: int | None, product_id: int | None = None) -> None:
        self.vendor_id = vendor_id
        self.product_id = product_id

        self._dev = self.get_device(vendor_id, product_id)

    def refresh(self) -> None:
        self._dev = self.get_device(self.vendor_id, self.product_id)

    @staticmethod
    def get_device(
        vendor_id: int | None = None, product_id: int | None = None
    ) -> usb.core.Device:
        """Get the PyUSB Device for a USB Printer"""
        if vendor_id and product_id:
            def match_func(dev) -> bool:
                return PyUSBBackend.has_vendor_product_id(dev, vendor_id, product_id)
        else:
            match_func = PyUSBBackend.is_usb_printer

        dev = usb.core.find(custom_match=match_func)
        if dev is None:
            raise BrotherPrinterError("No Printer Found")
        return dev

    @staticmethod
    def is_usb_printer(dev) -> bool:
        """Check if the Device is a USB Printer - by Device Class or Interface Class"""
        if dev.bDeviceClass == 7:
            return True
        for cfg in dev:
            if usb.util.find_descriptor(cfg, bInterfaceClass=7) is not None:
                return True
        return False

    @staticmethod
    def is_brother_manufacturer(dev) -> bool:
        """Check if the Device is a Brother Printer - by Manufacturer"""
        try:
            manufacturer = usb.util.get_string(dev, dev.iManufacturer)
        except (usb.core.USBError, ValueError):
            manufacturer = None

        if manufacturer == "Brother":
            return True
        return False

    @staticmethod
    def has_vendor_product_id(dev, vendor_id: int, product_id: int) -> bool:
        """Check if the Device has the given Vendor and Product ID"""
        return dev.idVendor == vendor_id and dev.idProduct == product_id

    def detach_from_kernel(self) -> None:
        """
        Detach the given Device from the Kernel - allowing PyUSB Exclusive Access
        Required for: usb.core.USBError: [Errno 16] Resource busy
        """
        self._dev.reset()

        interface = self._dev[0].interfaces()[0].bInterfaceNumber
        if self._dev.is_kernel_driver_active(interface):
            try:
                self._dev.detach_kernel_driver(interface)
            except usb.core.USBError:
                pass

        self._dev.set_configuration()

        self.refresh()

    def write(self, data: bytes, timeout: int = 1000) -> None:
        """Timeout - Default PyUSB Read Timeout is 1000ms=1s"""
        self._dev.write(endpoint=0x2, data=data, timeout=timeout)

    def read(self, count: int) -> bytes | None:
        for i in range(0, 3):
            data = self._dev.read(endpoint=0x81, size_or_buffer=count)
            if data:
                return data
            sleep(0.1)
        return None


def handle_error(e: Exception) -> None:
    """Handle the Exception from labelprinterkit or PyUSB"""
    if isinstance(e, usb.core.USBError):
        match e.errno:
            case 16:
                raise BrotherPrinterError(
                    "USB Device is Busy - Detach from Kernel"
                ) from e
            case 19:
                raise BrotherPrinterError(
                    "USB Device is Disconnected - Turn the Device On"
                ) from e
    raise e
