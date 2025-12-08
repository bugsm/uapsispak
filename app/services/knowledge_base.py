import json
import os

# Path to knowledge base JSON file
KB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "knowledge_base.json")

def load_knowledge_base():
    """Load knowledge base from JSON file."""
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_symptoms():
    """Get list of all symptoms."""
    kb = load_knowledge_base()
    return kb.get("symptoms", [])

def get_nutrients():
    """Get list of all nutrients."""
    kb = load_knowledge_base()
    return kb.get("nutrients", [])

def get_rules():
    """Get list of all rules (symptom-nutrient mappings with CF values)."""
    kb = load_knowledge_base()
    return kb.get("rules", [])

def get_nutrient_details(nutrient_code):
    """Get detailed information about a specific nutrient."""
    kb = load_knowledge_base()
    nutrients = kb.get("nutrients", [])
    for nutrient in nutrients:
        if nutrient["code"] == nutrient_code:
            return nutrient
    return None

