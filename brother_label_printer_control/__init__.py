from __future__ import annotations

__all__ = ["printers", "backends", "label", "job", "page"]

from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # Package - NOT Installed
    pass


class BrotherPrinterError(Exception):
    pass
