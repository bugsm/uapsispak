"""Knowledge Base Service - Akses dan validasi data knowledge base"""

import json
import os
import logging
from typing import Dict, List, Optional, Any

# Setup logger
logger = logging.getLogger(__name__)

# Path to knowledge base JSON file
KB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    "data", 
    "knowledge_base.json"
)

# Cache untuk knowledge base (mencegah multiple file reads)
_kb_cache: Optional[Dict[str, Any]] = None


class KnowledgeBaseError(Exception):
    """Custom exception untuk error pada knowledge base"""
    pass


class KnowledgeBaseValidationError(KnowledgeBaseError):
    """Exception untuk error validasi struktur knowledge base"""
    pass


def _validate_knowledge_base_structure(kb: Dict[str, Any]) -> bool:
    """
    Validasi struktur knowledge base JSON.
    
    Args:
        kb: Dictionary knowledge base yang akan divalidasi
        
    Returns:
        bool: True jika struktur valid
        
    Raises:
        KnowledgeBaseValidationError: Jika struktur tidak valid
    """
    required_keys = ["symptoms", "nutrients", "rules"]
    
    # Validasi keys utama
    for key in required_keys:
        if key not in kb:
            raise KnowledgeBaseValidationError(
                f"Knowledge base tidak memiliki key '{key}' yang diperlukan"
            )
        if not isinstance(kb[key], list):
            raise KnowledgeBaseValidationError(
                f"Key '{key}' harus berupa list, ditemukan: {type(kb[key])}"
            )
    
    # Validasi struktur symptoms
    symptom_codes = set()
    for idx, symptom in enumerate(kb["symptoms"]):
        if not isinstance(symptom, dict):
            raise KnowledgeBaseValidationError(
                f"Symptom pada index {idx} harus berupa dictionary"
            )
        required_symptom_keys = ["code", "name", "category"]
        for key in required_symptom_keys:
            if key not in symptom:
                raise KnowledgeBaseValidationError(
                    f"Symptom pada index {idx} tidak memiliki key '{key}'"
                )
        if symptom["code"] in symptom_codes:
            raise KnowledgeBaseValidationError(
                f"Duplicate symptom code: {symptom['code']}"
            )
        symptom_codes.add(symptom["code"])
    
    # Validasi struktur nutrients
    nutrient_codes = set()
    for idx, nutrient in enumerate(kb["nutrients"]):
        if not isinstance(nutrient, dict):
            raise KnowledgeBaseValidationError(
                f"Nutrient pada index {idx} harus berupa dictionary"
            )
        required_nutrient_keys = ["code", "name", "solusi"]
        for key in required_nutrient_keys:
            if key not in nutrient:
                raise KnowledgeBaseValidationError(
                    f"Nutrient pada index {idx} tidak memiliki key '{key}'"
                )
        if nutrient["code"] in nutrient_codes:
            raise KnowledgeBaseValidationError(
                f"Duplicate nutrient code: {nutrient['code']}"
            )
        nutrient_codes.add(nutrient["code"])
    
    # Validasi struktur rules
    valid_symptom_codes = symptom_codes
    valid_nutrient_codes = nutrient_codes
    
    for idx, rule in enumerate(kb["rules"]):
        if not isinstance(rule, dict):
            raise KnowledgeBaseValidationError(
                f"Rule pada index {idx} harus berupa dictionary"
            )
        required_rule_keys = ["nutrient", "symptom", "cf"]
        for key in required_rule_keys:
            if key not in rule:
                raise KnowledgeBaseValidationError(
                    f"Rule pada index {idx} tidak memiliki key '{key}'"
                )
        
        # Validasi referensi
        if rule["nutrient"] not in valid_nutrient_codes:
            raise KnowledgeBaseValidationError(
                f"Rule pada index {idx} memiliki nutrient code '{rule['nutrient']}' "
                f"yang tidak ada di nutrients"
            )
        if rule["symptom"] not in valid_symptom_codes:
            raise KnowledgeBaseValidationError(
                f"Rule pada index {idx} memiliki symptom code '{rule['symptom']}' "
                f"yang tidak ada di symptoms"
            )
        
        # Validasi CF value (harus antara 0 dan 1)
        try:
            cf_value = float(rule["cf"])
            if not (0.0 <= cf_value <= 1.0):
                raise KnowledgeBaseValidationError(
                    f"Rule pada index {idx} memiliki CF value {cf_value} "
                    f"di luar range 0.0-1.0"
                )
        except (ValueError, TypeError):
            raise KnowledgeBaseValidationError(
                f"Rule pada index {idx} memiliki CF value yang tidak valid: {rule['cf']}"
            )
    
    logger.info("Knowledge base structure validation passed")
    return True


def load_knowledge_base(use_cache: bool = True) -> Dict[str, Any]:
    """
    Load knowledge base dari JSON file dengan caching.
    
    Args:
        use_cache: Jika True, gunakan cache jika tersedia
        
    Returns:
        dict: Dictionary knowledge base yang berisi symptoms, nutrients, dan rules
        
    Raises:
        KnowledgeBaseError: Jika file tidak ditemukan atau error saat membaca
        KnowledgeBaseValidationError: Jika struktur data tidak valid
    """
    global _kb_cache
    
    # Return cache jika tersedia dan use_cache=True
    if use_cache and _kb_cache is not None:
        logger.debug("Using cached knowledge base")
        return _kb_cache
    
    # Validasi file exists
    if not os.path.exists(KB_PATH):
        error_msg = f"Knowledge base file tidak ditemukan: {KB_PATH}"
        logger.error(error_msg)
        raise KnowledgeBaseError(error_msg)
    
    try:
        # Load JSON file
        with open(KB_PATH, "r", encoding="utf-8") as f:
            kb_data = json.load(f)
        
        logger.info(f"Knowledge base loaded from {KB_PATH}")
        
        # Validasi struktur
        _validate_knowledge_base_structure(kb_data)
        
        # Update cache
        if use_cache:
            _kb_cache = kb_data
        
        return kb_data
        
    except json.JSONDecodeError as e:
        error_msg = f"Error parsing JSON file {KB_PATH}: {str(e)}"
        logger.error(error_msg)
        raise KnowledgeBaseError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error loading knowledge base: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise KnowledgeBaseError(error_msg)


def clear_cache() -> None:
    """Clear knowledge base cache (untuk testing atau reload)."""
    global _kb_cache
    _kb_cache = None
    logger.debug("Knowledge base cache cleared")


def get_symptoms() -> List[Dict[str, str]]:
    """
    Get list of all symptoms dari knowledge base.
    
    Returns:
        list: List of dictionaries, setiap dictionary berisi code, name, dan category
        
    Raises:
        KnowledgeBaseError: Jika error saat loading knowledge base
    """
    try:
        kb = load_knowledge_base()
        symptoms = kb.get("symptoms", [])
        logger.debug(f"Retrieved {len(symptoms)} symptoms")
        return symptoms
    except Exception as e:
        logger.error(f"Error getting symptoms: {str(e)}")
        raise


def get_nutrients() -> List[Dict[str, str]]:
    """
    Get list of all nutrients dari knowledge base.
    
    Returns:
        list: List of dictionaries, setiap dictionary berisi code, name, dan solusi
        
    Raises:
        KnowledgeBaseError: Jika error saat loading knowledge base
    """
    try:
        kb = load_knowledge_base()
        nutrients = kb.get("nutrients", [])
        logger.debug(f"Retrieved {len(nutrients)} nutrients")
        return nutrients
    except Exception as e:
        logger.error(f"Error getting nutrients: {str(e)}")
        raise


def get_rules() -> List[Dict[str, Any]]:
    """
    Get list of all rules (symptom-nutrient mappings dengan CF values).
    
    Returns:
        list: List of dictionaries, setiap dictionary berisi nutrient, symptom, dan cf
        
    Raises:
        KnowledgeBaseError: Jika error saat loading knowledge base
    """
    try:
        kb = load_knowledge_base()
        rules = kb.get("rules", [])
        logger.debug(f"Retrieved {len(rules)} rules")
        return rules
    except Exception as e:
        logger.error(f"Error getting rules: {str(e)}")
        raise


def get_nutrient_details(nutrient_code: str) -> Optional[Dict[str, str]]:
    """
    Get detailed information tentang nutrient tertentu berdasarkan code.
    
    Args:
        nutrient_code: Code nutrient (contoh: "D01", "D02")
        
    Returns:
        dict atau None: Dictionary berisi code, name, dan solusi jika ditemukan,
                       None jika tidak ditemukan
        
    Raises:
        KnowledgeBaseError: Jika error saat loading knowledge base
    """
    try:
        if not nutrient_code or not isinstance(nutrient_code, str):
            logger.warning(f"Invalid nutrient_code: {nutrient_code}")
            return None
            
        kb = load_knowledge_base()
        nutrients = kb.get("nutrients", [])
        
        for nutrient in nutrients:
            if nutrient.get("code") == nutrient_code:
                logger.debug(f"Found nutrient details for {nutrient_code}")
                return nutrient
        
        logger.warning(f"Nutrient code '{nutrient_code}' not found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting nutrient details for {nutrient_code}: {str(e)}")
        raise


def get_symptom_details(symptom_code: str) -> Optional[Dict[str, str]]:
    """
    Get detailed information tentang symptom tertentu berdasarkan code.
    
    Args:
        symptom_code: Code symptom (contoh: "G01", "G02")
        
    Returns:
        dict atau None: Dictionary berisi code, name, dan category jika ditemukan,
                       None jika tidak ditemukan
        
    Raises:
        KnowledgeBaseError: Jika error saat loading knowledge base
    """
    try:
        if not symptom_code or not isinstance(symptom_code, str):
            logger.warning(f"Invalid symptom_code: {symptom_code}")
            return None
            
        kb = load_knowledge_base()
        symptoms = kb.get("symptoms", [])
        
        for symptom in symptoms:
            if symptom.get("code") == symptom_code:
                logger.debug(f"Found symptom details for {symptom_code}")
                return symptom
        
        logger.warning(f"Symptom code '{symptom_code}' not found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting symptom details for {symptom_code}: {str(e)}")
        raise


def validate_symptom_codes(symptom_codes: List[str]) -> tuple[List[str], List[str]]:
    """
    Validasi list symptom codes terhadap knowledge base.
    
    Args:
        symptom_codes: List of symptom codes untuk divalidasi
        
    Returns:
        tuple: (valid_codes, invalid_codes) - dua list terpisah
        
    Raises:
        KnowledgeBaseError: Jika error saat loading knowledge base
    """
    try:
        kb = load_knowledge_base()
        valid_symptom_codes = {s["code"] for s in kb.get("symptoms", [])}
        
        valid = [code for code in symptom_codes if code in valid_symptom_codes]
        invalid = [code for code in symptom_codes if code not in valid_symptom_codes]
        
        if invalid:
            logger.warning(f"Invalid symptom codes found: {invalid}")
        
        return valid, invalid
        
    except Exception as e:
        logger.error(f"Error validating symptom codes: {str(e)}")
        raise
