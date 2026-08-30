#!/usr/bin/env python3
"""从服务器字体副本生成落霞孤鹜原版与 Word Regular 兼容版描述文件。"""
from pathlib import Path

from generate_profile import ROOT, make_profile


FONT_DIR = ROOT / "fonts" / "lxgw-ios"
OUT_DIR = ROOT / "profiles"

ORIGINAL_FONTS = [
    "LXGWWenKaiMonoScreen.ttf",
    "LXGWWenKaiMonoGBScreen.ttf",
    "LXGWWenKaiGBScreen.ttf",
    "LXGWWenKaiScreen.ttf",
    "LXGWNeoZhiSongScreen.ttf",
    "LXGWNeoXiHeiScreenFull.ttf",
    "LXGWNeoZhiSongScreenFull.ttf",
    "LXGWNeoXiHeiScreen.ttf",
    "LXGWWenKai-Regular.ttf",
    "LXGWWenKaiMono-Light.ttf",
    "LXGWWenKaiMono-Medium.ttf",
    "LXGWWenKai-Light.ttf",
    "LXGWWenKai-Medium.ttf",
    "LXGWWenKaiMono-Regular.ttf",
]

WORD_REGULAR_FONTS = [
    "LXGWWenKaiMonoScreen-Regular.ttf",
    "LXGWWenKaiMonoGBScreen-Regular.ttf",
    "LXGWWenKaiGBScreen-Regular.ttf",
    "LXGWWenKaiScreen-Regular.ttf",
    "LXGWNeoZhiSongScreen-Regular.ttf",
    "LXGWNeoXiHeiScreenFull-Regular.ttf",
    "LXGWNeoZhiSongScreenFull-Regular.ttf",
    "LXGWNeoXiHeiScreen-Regular.ttf",
]


def require_fonts(names: list[str]) -> list[Path]:
    fonts = [FONT_DIR / name for name in names]
    missing = [path.name for path in fonts if not path.is_file()]
    if missing:
        raise SystemExit(f"服务器字体副本不存在：{', '.join(missing)}")
    return fonts


def write_profile(
    filename: str,
    name: str,
    font_names: list[str],
    description: str,
    profile_id: str,
) -> None:
    data = make_profile(
        name,
        require_fonts(font_names),
        description,
        profile_id=profile_id,
    )
    path = OUT_DIR / filename
    path.write_bytes(data)
    print(f"{path.name}  {len(font_names)}款  {len(data) / 1024 / 1024:.1f} MB")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_profile(
        "落霞孤鹜字体合集（14款）.mobileconfig",
        "collection14-original-v2",
        ORIGINAL_FONTS,
        "落霞孤鹜字体合集（原版14款）",
        "org.silentperson.lxgw-original-v2",
    )
    write_profile(
        "落霞孤鹜字体合集（Word Regular兼容版，8款）.mobileconfig",
        "collection8-word-regular",
        WORD_REGULAR_FONTS,
        "落霞孤鹜字体合集（Word Regular兼容版8款）",
        "org.silentperson.lxgw-word-regular",
    )


if __name__ == "__main__":
    main()
