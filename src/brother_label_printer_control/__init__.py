from __future__ import annotations

__all__ = ["backends", "job", "label", "page", "printers"]

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # Package - NOT Installed
    pass


class BrotherPrinterError(Exception):
    pass
