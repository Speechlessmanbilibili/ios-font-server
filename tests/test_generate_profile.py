import plistlib
import tempfile
import unittest
from pathlib import Path

from generate_profile import DEFAULT_FONT_DIRS, discover_fonts, display_name, make_profile


class DiscoverFontsTests(unittest.TestCase):
    def test_default_sources_are_five_static_families(self):
        self.assertEqual(len(DEFAULT_FONT_DIRS), 5)
        self.assertTrue(all(path.name == "static" for path in DEFAULT_FONT_DIRS))

    def test_static_font_display_names(self):
        self.assertEqual(
            display_name(Path("HanlinkSans-BoldItalic.ttf")),
            "Hanlink Sans BoldItalic",
        )
        self.assertEqual(
            display_name(Path("CJKPunctBridgeInterrobang-Regular.ttf")),
            "CJK Punct Bridge ?! Regular",
        )
        self.assertEqual(
            display_name(Path("ThGrotesk-SemiBold.ttf")),
            "Th Grotesk SemiBold",
        )

    def test_duplicate_filename_prefers_later_source_and_profile_ids_are_unique(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            legacy = root / "legacy"
            dedicated = root / "dedicated"
            legacy.mkdir()
            dedicated.mkdir()

            name = "ThGrotesk-Black.ttf"
            (legacy / name).write_bytes(b"legacy")
            preferred = dedicated / name
            preferred.write_bytes(b"dedicated")

            fonts = discover_fonts([legacy, dedicated])

            self.assertEqual(fonts, [preferred])
            profile = plistlib.loads(make_profile("test", fonts, "test"))
            identifiers = [item["PayloadIdentifier"] for item in profile["PayloadContent"]]
            self.assertEqual(len(identifiers), len(set(identifiers)))


if __name__ == "__main__":
    unittest.main()
