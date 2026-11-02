import json
import os
import tempfile
from pathlib import Path


def save_website_states(states, state_file="website_states.json"):
    """Save website states safely using an atomic file replacement."""
    state_file = Path(state_file)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=state_file.parent,
            prefix="website_states_",
            suffix=".tmp",
            delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(states, temp_file, indent=4)
            temp_file.flush()
            os.fsync(temp_file.fileno())

        os.replace(temp_path, state_file)

    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
