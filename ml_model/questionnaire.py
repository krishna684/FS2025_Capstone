"""
questionnaire.py — Rule-based identification logic for the Plant Pest Detector.
"""

import json
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(_BASE_DIR, "questionnaire_data.json")

def load_questionnaire():
    """Load the questionnaire data."""
    if not os.path.exists(_DATA_PATH):
        return {"questions": [], "mappings": []}
    with open(_DATA_PATH, "r") as f:
        return json.load(f)

def analyze_answers(answers: dict):
    """
    Analyze the provided answers against the pest mappings and return the best match.
    The answers dict should map question IDs to option values.
    """
    data = load_questionnaire()
    mappings = data.get("mappings", [])
    
    best_match = None
    max_score = 0
    
    # Simple scoring: each matching criterion adds 1 point
    for entry in mappings:
        pest_name = entry["pest"]
        criteria = entry["criteria"]
        score = 0
        
        for key, value in criteria.items():
            if answers.get(key) == value:
                score += 1
        
        if score > max_score:
            max_score = score
            best_match = pest_name
    
    # Return Top 1 match
    if best_match:
        return best_match
    return "Unknown Pest"
