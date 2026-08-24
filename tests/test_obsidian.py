import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gobs.obsidian import vault_uri  # noqa: E402


class UriTests(unittest.TestCase):
    def test_uri_contains_encoded_path(self) -> None:
        uri = vault_uri(Path("/tmp/My Vault"))
        self.assertTrue(uri.startswith("obsidian://open?path="))
        self.assertNotIn(" ", uri)


if __name__ == "__main__":
    unittest.main()
