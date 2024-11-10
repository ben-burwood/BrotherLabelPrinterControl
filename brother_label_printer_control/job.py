from __future__ import annotations

from .constants import Media, Resolution
from .page import PageType


class Job:
    def __init__(
        self,
        media: Media,
        auto_cut: bool = True,
        mirror_printing: bool = False,
        half_cut: bool = False,
        chain: bool = False,
        special_tape: bool = False,
        cut_each: int = 1,
        resolution: Resolution = Resolution.LOW,
    ):

        self.media = media

        self.auto_cut = auto_cut
        self.mirror_printing = mirror_printing
        self.half_cut = half_cut
        self.chain = chain
        self.special_tape = special_tape
        if not 1 <= cut_each <= 99:
            ValueError(f"cut_skip has to be between 1 and 99")
        self.cut_each = cut_each
        self.resolution = resolution

        self._pages = []

    def __iter__(self):
        return iter(self._pages)

    def __len__(self):
        return len(self._pages)

    def add_page(self, page: PageType):
        width = self.media.value.printarea
        if page.width != width:
            raise RuntimeError("Page width does not match media width")
        if page.resolution != self.resolution:
            raise RuntimeError("Page resolution does not match media resolution")
        if self.resolution == Resolution.LOW:
            min_length = 31
        else:
            min_length = 62
        if page.length < min_length:
            raise RuntimeError("Page is not long enough")
        self._pages.append(page)
