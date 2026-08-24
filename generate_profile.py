#!/usr/bin/env python3
"""生成 iOS 字体描述文件。

iOS 对配置描述文件有大小限制（约 15-20MB，实测经验），单个大 profile 会
报「包含无效字体」。因此：
- Hanlink Sans：按字重「正体+斜体」两两配对，生成 9 个 profile（每个
  ~22MB 原始 / ~29MB base64，用户实测两两可装）
- CJK Punct Bridge：全部 18 个静态放进一个 profile（~2.4MB base64，很小）
- 额外生成一个 187KB 的最小测试 profile 用于排查 iOS 报错
"""
import base64
import plistlib
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "profiles"
HANLINK = ROOT.parent / "hanlink-sans" / "fonts" / "static"
BRIDGE = ROOT.parent / "CJK-Punct-Bridge" / "fonts" / "static"
PROFILE_ID = "org.silentperson.hanlink-sans-cjkpunct"


def display_name(path: Path) -> str:
    name = path.stem
    if name.startswith("HanlinkSans-"):
        family, style = "Hanlink Sans", name[len("HanlinkSans-"):]
    else:
        family, style = "CJK Punct Bridge", name[len("CJKPunctBridge-"):]
    return f"{family} {style}".replace("  ", " ")


def make_profile(name: str, fonts: list, description: str) -> Path:
    payloads = []
    for path in fonts:
        payloads.append({
            "PayloadType": "com.apple.font",
            "PayloadVersion": 1,
            "PayloadIdentifier": f"{PROFILE_ID}.font.{path.stem}",
            "PayloadUUID": str(uuid.uuid4()),
            "PayloadDisplayName": display_name(path),
            # Name 是 com.apple.font 的必需键（字体文件名），缺失会被 iOS
            # 判定「包含无效字体」（参考 Apple 文档示例与 keyman 实测 profile）。
            "Name": path.name,
            "PayloadDescription": "Configures Font settings",
            # 必须传原始字体字节！plistlib 序列化时会自行 base64 编码；
            # 若先 b64encode 一次再传入，会形成双重 base64，iOS 解码后
            # 拿到的是 base64 文本而非字体数据，直接报「包含无效字体」。
            "Font": path.read_bytes(),
        })
    profile = {
        "PayloadType": "Configuration",
        "PayloadVersion": 1,
        "PayloadIdentifier": f"{PROFILE_ID}.{name}",
        "PayloadUUID": str(uuid.uuid4()),
        "PayloadDisplayName": description,
        "PayloadDescription": description,
        "PayloadContent": payloads,
    }
    out = OUT_DIR / f"{name}.mobileconfig"
    # 二进制 plist：Apple Configurator 生成的描述文件即为二进制格式，
    # data 存原始字节（无 base64/缩进问题），iOS 解析最稳。
    out.write_bytes(plistlib.dumps(profile, fmt=plistlib.FMT_BINARY))
    return out


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for p in OUT_DIR.glob("*.mobileconfig"):
        p.unlink()

    # 0) 全量：36 个字体一个大 profile，放页面最顶部
    all_fonts = sorted(HANLINK.glob("*.ttf")) + sorted(BRIDGE.glob("*.ttf"))
    assert len(all_fonts) == 36
    make_profile(
        "HanlinkSans-CJKPunctBridge-All",
        all_fonts,
        "Hanlink Sans + CJK Punct Bridge 全静态字体（36 个：9 正体 + 9 斜体 + 18 标点）",
    )

    # 1) 最小测试 profile（排查 iOS「包含无效字体」报错）
    make_profile(
        "test-CJKPunctBridge-Regular",
        [BRIDGE / "CJKPunctBridge-Regular.ttf"],
        "测试：CJK Punct Bridge Regular（单字体，187KB）",
    )

    # 2) CJK Punct Bridge 全家桶（18 个全装，很小）
    bridge_fonts = sorted(BRIDGE.glob("*.ttf"))
    assert len(bridge_fonts) == 18
    make_profile(
        "CJKPunctBridge-All",
        bridge_fonts,
        "CJK Punct Bridge 全静态标点（9 正体 + 9 斜体）",
    )

    # 3) Hanlink Sans 两两配对：同一字重的正体 + 斜体
    weights = {
        100: "Thin", 200: "ExtraLight", 300: "Light", 400: "Regular",
        500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold",
        900: "Black",
    }
    for w, style in weights.items():
        pair = [
            HANLINK / (f"HanlinkSans-{style}.ttf" if w != 400 else "HanlinkSans-Regular.ttf"),
            HANLINK / (f"HanlinkSans-Italic.ttf" if w == 400 else f"HanlinkSans-{style}Italic.ttf"),
        ]
        for p in pair:
            assert p.exists(), p
        make_profile(
            f"HanlinkSans-{style}+Italic",
            pair,
            f"Hanlink Sans {style} + {style} Italic",
        )

    results = sorted((p.stat().st_size / 1024 / 1024, p.name) for p in OUT_DIR.glob("*.mobileconfig"))
    for size, name in results:
        print(f"  {name:45s} {size:7.1f} MB")
    print(f"共 {len(results)} 个描述文件")


if __name__ == "__main__":
    main()
