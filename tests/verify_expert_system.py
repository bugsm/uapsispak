import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.inference_cf import calculate_cf

def test_cf_logic():
    print("Testing Expert System Logic...")
    
    # Test Case: Defisiensi Kalsium (D04)
    # Rules D04:
    # G19 (0.85)
    # G20 (0.93)
    # G21 (0.70)
    
    # User Input
    user_symptoms = {
        "G19": 0.8,
        "G20": 1.0,
        "G21": 0.6
    }
    
    print(f"User Input: {user_symptoms}")
    
    results = calculate_cf(user_symptoms)
    
    print("\nResults:")
    for nutrient, cf in results.items():
        if cf > 0:
            print(f"{nutrient}: {cf}")
            
    # Manual Calculation Check
    # CF1 (G19) = 0.85 * 0.8 = 0.68
    # CF2 (G20) = 0.93 * 1.0 = 0.93
    # CF3 (G21) = 0.70 * 0.6 = 0.42
    
    # Combine 1 & 2
    # CF_comb1 = 0.68 + 0.93 * (1 - 0.68) = 0.68 + 0.2976 = 0.9776
    
    # Combine with 3
    # CF_comb2 = 0.9776 + 0.42 * (1 - 0.9776) = 0.9776 + 0.42 * 0.0224 = 0.9776 + 0.009408 = 0.987008
    
    # Round to 4 decimals: 0.987
    
    expected_d04 = 0.987
    actual_d04 = results.get("D04", 0)
    
    print(f"\nExpected D04: {expected_d04}")
    print(f"Actual D04:   {actual_d04}")
    
    success = abs(actual_d04 - expected_d04) < 0.001
    
    if success:
        print("\n[SUCCESS] Logic verified correct.")
    else:
        print("\n[FAILURE] Logic mismatch.")

if __name__ == "__main__":
    test_cf_logic()
