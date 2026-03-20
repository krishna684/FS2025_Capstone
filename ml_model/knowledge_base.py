"""
knowledge_base.py — Load and query the pest knowledge base.
"""

import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "pest_data.json")

_pest_db: dict | None = None


def _load():
    global _pest_db
    if _pest_db is None:
        with open(_DATA_PATH, "r") as f:
            _pest_db = json.load(f)
    return _pest_db


def get_all_pest_names() -> list[str]:
    """Return the ordered list of pest class names."""
    db = _load()
    return [p["name"] for p in db["pests"]]


def get_pest_info(class_index: int) -> dict:
    """Return full info dict for the given class index."""
    db = _load()
    if 0 <= class_index < len(db["pests"]):
        return db["pests"][class_index]
    return {}


def get_pest_info_by_name(name: str) -> dict:
    """Return full info dict for the given pest name (case-insensitive)."""
    db = _load()
    for pest in db["pests"]:
        if pest["name"].lower() == name.lower():
            return pest
    return {}


def get_num_classes() -> int:
    """Return the total number of pest classes."""
    db = _load()
    return len(db["pests"])
