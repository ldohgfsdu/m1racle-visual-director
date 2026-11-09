"""Package ZIP determinism and integrity checks, no network or model required."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_release as release


class DeterministicReleaseTests(unittest.TestCase):
    def test_two_clean_builds_have_exact_same_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            one, two = Path(root) / "a", Path(root) / "b"
            z1, c1 = release.build(ROOT, one)
            z2, c2 = release.build(ROOT, two)
            self.assertEqual(z1.read_bytes(), z2.read_bytes())
            self.assertEqual(c1.read_bytes(), c2.read_bytes())
            self.assertEqual(
                c1.read_text(encoding="ascii"),
                hashlib.sha256(z1.read_bytes()).hexdigest() + "  " + z1.name + "\n",
            )

    def test_archive_contains_complete_payload_and_fixed_timestamps(self):
        with tempfile.TemporaryDirectory() as root:
            archive, _ = release.build(ROOT, Path(root))
            with ZipFile(archive) as z:
                names = z.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertIn("m1racle-intaglio-director/MANIFEST.json", names)
                for info in z.infolist():
                    self.assertEqual(info.date_time, release.STAMP)
                    self.assertTrue(info.filename.startswith(release.PREFIX))


if __name__ == "__main__":
    unittest.main()
