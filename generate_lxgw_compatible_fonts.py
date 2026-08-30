#!/usr/bin/env python3
"""由未修改的服务器副本生成保留多语言名称的 Word Regular 兼容字体。"""
import os
from pathlib import Path

from fontTools.ttLib import TTFont

from generate_profile import ROOT


FONT_DIR = ROOT / "fonts" / "lxgw-ios"
SOURCE_NAMES = [
    "LXGWWenKaiMonoScreen.ttf",
    "LXGWWenKaiMonoGBScreen.ttf",
    "LXGWWenKaiGBScreen.ttf",
    "LXGWWenKaiScreen.ttf",
    "LXGWNeoZhiSongScreen.ttf",
    "LXGWNeoXiHeiScreenFull.ttf",
    "LXGWNeoZhiSongScreenFull.ttf",
    "LXGWNeoXiHeiScreen.ttf",
]


def with_regular(value: str, separator: str = " ") -> str:
    suffix = f"{separator}Regular"
    return value if value.endswith(suffix) else f"{value}{suffix}"


def make_compatible_font(source: Path, destination: Path) -> None:
    font = TTFont(source)
    names = font["name"]

    # 直接更新每条既有记录，保留原平台、编码和语言。这样中文名及源字体中
    # 可能存在的其他本地化名称不会被英文记录取代。
    for record in names.names:
        if record.nameID in (1, 3, 4):
            record.string = with_regular(record.toUnicode()).encode(record.getEncoding())
        elif record.nameID == 6:
            record.string = with_regular(
                record.toUnicode(), separator="-"
            ).encode(record.getEncoding())

    temp = destination.with_suffix(".tmp.ttf")
    font.save(temp, reorderTables=False)
    font.close()
    os.replace(temp, destination)


def main() -> None:
    for source_name in SOURCE_NAMES:
        source = FONT_DIR / source_name
        if not source.is_file():
            raise SystemExit(f"未修改的服务器字体副本不存在：{source.name}")
        destination = source.with_name(f"{source.stem}-Regular.ttf")
        make_compatible_font(source, destination)
        print(f"{source.name} -> {destination.name}")


if __name__ == "__main__":
    main()
