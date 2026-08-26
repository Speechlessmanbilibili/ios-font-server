import plistlib
import tempfile
import unittest
from pathlib import Path

from generate_profile import discover_fonts, make_profile


class DiscoverFontsTests(unittest.TestCase):
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
