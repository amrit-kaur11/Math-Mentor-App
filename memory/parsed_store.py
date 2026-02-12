import json
import os
from datetime import datetime, timezone


PARSED_MEMORY_DIR = "data/memory"
PARSED_MEMORY_FILE = os.path.join(PARSED_MEMORY_DIR, "step2_parsed_logs.json")


def initialize_parsed_memory():
    """
    Initialize parsed memory file if it doesn't exist.
    """
    os.makedirs(PARSED_MEMORY_DIR, exist_ok=True)

    if not os.path.exists(PARSED_MEMORY_FILE):
        with open(PARSED_MEMORY_FILE, "w") as f:
            json.dump([], f)


def store_parsed_record(verified_text: str, parsed_output: dict):
    """
    Store parsed output from Step-2.

    Args:
        verified_text (str): Final verified question
        parsed_output (dict): Structured parser output
    """

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verified_text": verified_text,
        "parsed_output": parsed_output
    }

    with open(PARSED_MEMORY_FILE, "r") as f:
        memory = json.load(f)

    if not isinstance(memory, list):
        memory = []    

    memory.append(record)

    with open(PARSED_MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)
