import os
from pathlib import Path
from typing import NewType

FontPath = NewType("FontPath", Path)


LINUX_TRUETYPE_FONT_DIRECTORY = "/usr/share/fonts/truetype"


def get_fonts(font_path: str | Path = LINUX_TRUETYPE_FONT_DIRECTORY) -> dict[str, list[FontPath]]:
    """Get all Paths to Linux Fonts : Dict with Key as the Font Name and Value as a List of Paths of Font Variants"""
    fonts = {}
    for font in os.listdir(font_path):
        fonts[font] = []
        for font_variant in os.listdir(f"{font_path}/{font}"):
            fonts[font].append(FontPath(Path(f"{font_path}/{font}/{font_variant}")))
    return fonts
