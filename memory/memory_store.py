import json
import os
from datetime import datetime, timezone


MEMORY_DIR = "data/memory"
MEMORY_FILE = os.path.join(MEMORY_DIR, "step1_logs.json")


def initialize_memory():
    """
    Initialize memory directory and file if they don't exist.
    """
    os.makedirs(MEMORY_DIR, exist_ok=True)

    if not os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "w") as f:
            json.dump([], f)


def store_step1_record(
    input_type: str,
    raw_input_ref: str,
    extracted_text: str,
    verified_text: str,
    confidence: float,
    hitl_used: bool
):
    """
    Stores a Step 1 interaction record.

    Args:
        input_type (str): 'text', 'image', or 'audio'
        raw_input_ref (str): Reference to raw input (filename or inline)
        extracted_text (str): Text produced by OCR / ASR / direct input
        verified_text (str): Final user-approved text
        confidence (float): Confidence score
        hitl_used (bool): Whether HITL was triggered
    """

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_type": input_type,
        "raw_input_ref": raw_input_ref,
        "extracted_text": extracted_text,
        "verified_text": verified_text,
        "confidence": confidence,
        "hitl_used": hitl_used
    }

    # Load existing memory
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)

    # Append new record
    memory.append(record)

    # Save back to file
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)
