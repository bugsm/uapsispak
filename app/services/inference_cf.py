"""Certainty Factor Inference Service - Implementasi CF untuk sistem pakar tomat"""

import logging
from typing import Dict, Optional, List, Tuple
from app.services.knowledge_base import (
    get_rules, 
    get_nutrients, 
    get_symptoms,
    validate_symptom_codes,
    get_symptom_details,
    KnowledgeBaseError
)

# Setup logger
logger = logging.getLogger(__name__)


class InferenceError(Exception):
    """Custom exception untuk error pada inference CF"""
    pass


def _validate_selected_symptoms(selected_symptoms: Dict[str, float]) -> Dict[str, float]:
    """Validasi dan normalisasi gejala yang dipilih"""
    if not isinstance(selected_symptoms, dict):
        raise InferenceError(
            f"selected_symptoms harus berupa dictionary, "
            f"ditemukan: {type(selected_symptoms)}"
        )
    
    if len(selected_symptoms) == 0:
        logger.warning("No symptoms selected")
        return {}
    
    # Validasi symptom codes terhadap knowledge base
    symptom_codes = list(selected_symptoms.keys())
    valid_codes, invalid_codes = validate_symptom_codes(symptom_codes)
    
    if invalid_codes:
        logger.warning(f"Removing invalid symptom codes: {invalid_codes}")
    
    # Filter hanya valid codes dan validasi CF values
    validated = {}
    for code in valid_codes:
        cf_value = selected_symptoms[code]
        
        # Convert ke float jika mungkin
        try:
            cf_float = float(cf_value)
        except (ValueError, TypeError):
            logger.warning(f"Invalid CF value for {code}: {cf_value}, skipping")
            continue
        
        # Validasi range (0.0 - 1.0) sesuai teori CF
        if not (0.0 <= cf_float <= 1.0):
            logger.warning(
                f"CF value for {code} ({cf_float}) out of range [0.0, 1.0], "
                f"clamping to valid range"
            )
            cf_float = max(0.0, min(1.0, cf_float))
        
        validated[code] = cf_float
    
    if len(validated) == 0:
        logger.warning("No valid symptoms after validation")
    
    logger.info(f"Validated {len(validated)} symptoms out of {len(selected_symptoms)}")
    return validated


def _calculate_rule_cf(cf_pakar: float, cf_user: float) -> float:
    """Hitung CF untuk satu rule: CF = CF_pakar * CF_user"""
    # Validasi range
    cf_pakar = max(0.0, min(1.0, cf_pakar))
    cf_user = max(0.0, min(1.0, cf_user))
    
    # Formula dasar CF: CF(H,E) = CF_pakar * CF_user
    cf_rule = cf_pakar * cf_user
    
    return cf_rule


def _combine_multiple_cf(cf_list: List[float]) -> Tuple[float, List[Dict]]:
    """Kombinasikan multiple CF: CF_combined = CF_old + CF_new * (1 - CF_old)"""
    if not cf_list:
        return 0.0, []
    
    if len(cf_list) == 1:
        return cf_list[0], []
    
    # Mulai dengan CF pertama
    cf_combined = cf_list[0]
    steps = []
    
    # Kombinasikan dengan CF berikutnya satu per satu
    for idx, cf_next in enumerate(cf_list[1:], start=1):
        cf_old_before = cf_combined
        # Formula: CF_combined = CF_old + CF_new * (1 - CF_old)
        cf_combined = cf_combined + cf_next * (1 - cf_combined)
        
        steps.append({
            'step': idx,
            'cf_old': round(cf_old_before, 4),
            'cf_new': round(cf_next, 4),
            'calculation': f"{cf_old_before:.4f} + {cf_next:.4f} * (1 - {cf_old_before:.4f})",
            'result': round(cf_combined, 4)
        })
    
    return cf_combined, steps


def calculate_cf_with_details(
    selected_symptoms: Dict[str, float],
    validate_input: bool = True
) -> Tuple[Dict[str, float], Dict[str, Dict]]:
    """Hitung CF dengan detail lengkap untuk setiap nutrient"""
    if validate_input:
        selected_symptoms = _validate_selected_symptoms(selected_symptoms)
    
    if not selected_symptoms:
        nutrients = get_nutrients()
        return (
            {n['code']: 0.0 for n in nutrients},
            {n['code']: {'rules_used': [], 'cf_final': 0.0, 'steps': []} for n in nutrients}
        )
    
    try:
        rules = get_rules()
        nutrients = get_nutrients()
        symptoms_list = get_symptoms()
        
        symptoms_data = {}
        for s in symptoms_list:
            if isinstance(s, dict) and 'code' in s:
                symptoms_data[s['code']] = s
            else:
                logger.warning(f"Invalid symptom data: {s}")
                
    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}", exc_info=True)
        raise InferenceError(f"Error loading knowledge base: {str(e)}")
    
    nutrient_cfs = {}
    calculation_details = {}
    
    for nutrient in nutrients:
        n_code = nutrient['code']
        n_name = nutrient['name']
        
        nutrient_rules = [r for r in rules if r['nutrient'] == n_code]
        rules_used = []
        cf_list = []
        
        for rule in nutrient_rules:
            s_code = rule['symptom']
            
            if s_code in selected_symptoms:
                cf_pakar = float(rule['cf'])
                cf_user = float(selected_symptoms[s_code])
                
                if cf_user > 0:
                    cf_rule = _calculate_rule_cf(cf_pakar, cf_user)
                    
                    symptom_info = symptoms_data.get(s_code, {'name': s_code, 'category': 'Unknown'})
                    
                    rules_used.append({
                        'symptom_code': s_code,
                        'symptom_name': symptom_info['name'],
                        'symptom_category': symptom_info.get('category', 'Unknown'),
                        'cf_pakar': round(cf_pakar, 4),
                        'cf_user': round(cf_user, 4),
                        'cf_rule': round(cf_rule, 4),
                        'formula': f"{cf_pakar:.4f} * {cf_user:.4f} = {cf_rule:.4f}"
                    })
                    
                    cf_list.append(cf_rule)
        
        if cf_list:
            cf_final, combination_steps = _combine_multiple_cf(cf_list)
            nutrient_cfs[n_code] = round(cf_final, 4)
        else:
            cf_final = 0.0
            combination_steps = []
            nutrient_cfs[n_code] = 0.0
        
        calculation_details[n_code] = {
            'nutrient_code': n_code,
            'nutrient_name': n_name,
            'rules_used': rules_used,
            'cf_list': [round(cf, 4) for cf in cf_list],
            'combination_steps': combination_steps,
            'cf_final': round(cf_final, 4),
            'cf_percentage': round(cf_final * 100, 2)
        }
    
    return nutrient_cfs, calculation_details


def calculate_cf(
    selected_symptoms: Dict[str, float],
    validate_input: bool = True
) -> Dict[str, float]:
    """Hitung CF untuk setiap nutrient berdasarkan gejala yang dipilih"""
    cf_results, _ = calculate_cf_with_details(selected_symptoms, validate_input)
    return cf_results


def get_top_nutrient(cf_results: Dict[str, float]) -> Optional[Tuple[str, float]]:
    """Get nutrient dengan CF tertinggi"""
    if not cf_results:
        return None
    
    max_cf = max(cf_results.values())
    
    if max_cf == 0.0:
        return None
    
    max_nutrient = max(cf_results, key=cf_results.get)
    return (max_nutrient, max_cf)
