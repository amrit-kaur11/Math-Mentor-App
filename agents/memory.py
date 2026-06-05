import sqlite3
import os
import re
from typing import List, Dict, Any


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "db", "memory.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_input TEXT,
            parsed_question TEXT,
            topic TEXT,
            retrieved_context TEXT,
            final_answer TEXT,
            verifier_outcome TEXT,
            user_feedback TEXT,
            feedback_comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        '''
    )

    conn.commit()
    conn.close()


def save_interaction(data: dict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        INSERT INTO interactions (
            raw_input, parsed_question, topic, retrieved_context,
            final_answer, verifier_outcome, user_feedback, feedback_comment
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            data.get("raw_input", ""),
            data.get("parsed_question", ""),
            data.get("topic", ""),
            data.get("retrieved_context", ""),
            data.get("final_answer", ""),
            data.get("verifier_outcome", ""),
            data.get("user_feedback", ""),
            data.get("feedback_comment", ""),
        ),
    )

    conn.commit()
    conn.close()


def _clean_inline(text: str, max_len: int = 90) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    cleaned = re.sub(r"#+\s*", "", cleaned).strip()

    if len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 3].rstrip() + "..."

    return cleaned


def make_history_title(raw_input: str, parsed_question: str = "") -> str:
    """
    Creates a short ChatGPT-style title for the sidebar.
    """
    source = parsed_question or raw_input or "Math problem"

    title = _clean_inline(source, max_len=46)
    title = re.sub(
        r"^(solve|find|calculate|differentiate|integrate|simplify)\s*:?\s*",
        "",
        title,
        flags=re.IGNORECASE,
    ).strip()

    return title or "Math problem"


def get_similar_past_problems(topic: str, limit: int = 3):
    """
    Retrieves past solved problems that were marked correct for a given topic.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT parsed_question, final_answer
        FROM interactions
        WHERE topic = ? AND user_feedback = "correct"
        ORDER BY timestamp DESC LIMIT ?
        ''',
        (topic, limit),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""

    memory_context = "### Previous Correct Similar Problems:\n"
    for q, a in rows:
        memory_context += f"- Q: {_clean_inline(q, 120)}\n  A: {_clean_inline(a, 120)}\n"

    return memory_context


def get_recent_history(limit: int = 5):
    """
    Retrieves recent history as a compact prompt context.

    This intentionally does not return full solutions because that made the
    sidebar and router prompt noisy.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT raw_input, final_answer
        FROM interactions
        ORDER BY timestamp DESC LIMIT ?
        ''',
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""

    history_context = "### Recent Conversation History:\n"
    for q, a in reversed(rows):
        history_context += f"- User: {_clean_inline(q, 100)}\n  Answer: {_clean_inline(a, 100)}\n"

    return history_context


def get_recent_history_items(limit: int = 12) -> List[Dict[str, Any]]:
    """
    Returns structured recent items for a ChatGPT-style sidebar.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT id, raw_input, parsed_question, topic, final_answer, timestamp
        FROM interactions
        ORDER BY timestamp DESC LIMIT ?
        ''',
        (limit,),
    )

    rows = cursor.fetchall()
    conn.close()

    items = []
    for row in rows:
        item_id, raw_input, parsed_question, topic, final_answer, timestamp = row
        items.append(
            {
                "id": item_id,
                "title": make_history_title(raw_input, parsed_question),
                "raw_input": raw_input or "",
                "parsed_question": parsed_question or "",
                "topic": topic or "",
                "final_answer": final_answer or "",
                "timestamp": timestamp or "",
            }
        )

    return items
