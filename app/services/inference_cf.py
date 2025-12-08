from app.services.knowledge_base import get_rules, get_nutrients

def calculate_cf(selected_symptoms):
    """
    Calculates Certainty Factor for each nutrient based on selected symptoms and user confidence.
    
    Args:
        selected_symptoms (dict): Dict of {symptom_code: cf_user_value}
                                 e.g., {'G01': 0.8, 'G03': 0.6}
        
    Returns:
        dict: {nutrient_code: cf_value}
    """
    rules = get_rules()
    nutrients = get_nutrients()
    
    # Initialize CFs for all nutrients to 0
    nutrient_cfs = {n['code']: 0.0 for n in nutrients}
    
    # Group rules by nutrient
    for nutrient in nutrients:
        n_code = nutrient['code']
        current_cf = 0.0
        
        # 1. Collect all valid CFs for this nutrient from matching rules
        cf_gejala_list = []
        
        # Find all rules for this nutrient
        nutrient_rules = [r for r in rules if r['nutrient'] == n_code]
        
        for rule in nutrient_rules:
            s_code = rule['symptom']
            
            # Check if this symptom was selected by the user
            if s_code in selected_symptoms:
                cf_user = float(selected_symptoms[s_code])
                cf_pakar = float(rule['cf'])
                
                # CF(H,E) = CF_pakar * CF_user
                cf_current_rule = cf_pakar * cf_user
                cf_gejala_list.append(cf_current_rule)
        
        # 2. Combine CFs using: CF_new = CF_old + CF_new * (1 - CF_old)
        if cf_gejala_list:
            current_cf = cf_gejala_list[0]
            for next_cf in cf_gejala_list[1:]:
                current_cf = current_cf + next_cf * (1 - current_cf)
            
        nutrient_cfs[n_code] = round(current_cf, 4)
        
    return nutrient_cfs
