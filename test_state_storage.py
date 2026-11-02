import json
import tempfile
import unittest
from pathlib import Path

from state_storage import save_website_states


class TestStateStorage(unittest.TestCase):

    def test_save_website_states(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "website_states.json"

            states = {
                "https://example.com": "UP",
                "https://google.com": "DOWN"
            }

            save_website_states(states, test_file)

            saved_states = json.loads(
                test_file.read_text(encoding="utf-8")
            )

            self.assertEqual(saved_states, states)

    def test_update_existing_states(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "website_states.json"

            initial_states = {
                "https://example.com": "UP"
            }

            updated_states = {
                "https://example.com": "DOWN"
            }

            save_website_states(initial_states, test_file)
            save_website_states(updated_states, test_file)

            saved_states = json.loads(
                test_file.read_text(encoding="utf-8")
            )

            self.assertEqual(saved_states, updated_states)


if __name__ == "__main__":
    unittest.main()
