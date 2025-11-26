"""
Test script for IPM recommendation engine
"""

from app import app
from ipm_engine import get_recommendations, get_pest_by_name
import json


def test_ipm_engine():
    """Test the IPM recommendation engine"""
    with app.app_context():
        print("=" * 80)
        print("Testing IPM Recommendation Engine")
        print("=" * 80)
        
        # Test 1: Get recommendations for Fall Armyworm
        print("\n1. Testing Fall Armyworm recommendations (global, no crop):")
        print("-" * 80)
        pest = get_pest_by_name('Fall Armyworm')
        if pest:
            recommendations = get_recommendations(pest.id, region='global')
            print(f"Found {len(recommendations)} recommendations for {pest.common_name}")
            
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec['treatment_name']} ({rec['type']})")
                print(f"   Priority: {rec['priority']}")
                print(f"   Description: {rec['description'][:100]}...")
                if rec.get('is_last_resort'):
                    print(f"   ⚠️ LAST RESORT")
                if rec.get('safety_warning'):
                    print(f"   Warning: {rec['safety_warning'][:80]}...")
        else:
            print("Pest not found!")
        
        # Test 2: Get recommendations for Aphids with crop filter
        print("\n\n2. Testing Aphids recommendations (global, all crops):")
        print("-" * 80)
        pest = get_pest_by_name('Aphids')
        if pest:
            recommendations = get_recommendations(pest.id, crop='all', region='global')
            print(f"Found {len(recommendations)} recommendations for {pest.common_name}")
            
            # Group by type
            cultural = [r for r in recommendations if r['type'] == 'cultural']
            biological = [r for r in recommendations if r['type'] == 'biological']
            chemical = [r for r in recommendations if r['type'] == 'chemical']
            
            print(f"\nCultural controls: {len(cultural)}")
            for rec in cultural:
                print(f"  - {rec['treatment_name']} (priority: {rec['priority']})")
            
            print(f"\nBiological controls: {len(biological)}")
            for rec in biological:
                print(f"  - {rec['treatment_name']} (priority: {rec['priority']})")
            
            print(f"\nChemical controls: {len(chemical)}")
            for rec in chemical:
                print(f"  - {rec['treatment_name']} (priority: {rec['priority']}) ⚠️")
        
        # Test 3: Verify IPM priority ordering
        print("\n\n3. Testing IPM priority ordering:")
        print("-" * 80)
        pest = get_pest_by_name('Spider Mites')
        if pest:
            recommendations = get_recommendations(pest.id, region='global')
            print(f"Recommendations for {pest.common_name} (in order):")
            
            for i, rec in enumerate(recommendations, 1):
                type_icon = "🌱" if rec['type'] == 'cultural' else "🐛" if rec['type'] == 'biological' else "⚠️"
                print(f"{i}. {type_icon} {rec['treatment_name']} ({rec['type']}, {rec['priority']})")
            
            # Verify ordering
            types_in_order = [r['type'] for r in recommendations]
            print(f"\nType sequence: {' -> '.join(types_in_order)}")
            
            # Check that cultural/biological come before chemical
            chemical_indices = [i for i, r in enumerate(recommendations) if r['type'] == 'chemical']
            non_chemical_indices = [i for i, r in enumerate(recommendations) if r['type'] != 'chemical']
            
            if chemical_indices and non_chemical_indices:
                if min(chemical_indices) > max(non_chemical_indices):
                    print("✓ IPM ordering correct: Cultural/Biological before Chemical")
                else:
                    print("✗ IPM ordering incorrect: Chemical treatments not at end")
        
        # Test 4: Test localization
        print("\n\n4. Testing localization (Spanish):")
        print("-" * 80)
        pest = get_pest_by_name('Tomato Leafminer')
        if pest:
            recommendations = get_recommendations(pest.id, region='global', language='es')
            print(f"Recommendations for {pest.common_name} in Spanish:")
            
            for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                print(f"\n{i}. {rec['treatment_name']}")
                print(f"   {rec['description'][:100]}...")
        
        print("\n" + "=" * 80)
        print("IPM Engine Testing Complete")
        print("=" * 80)


if __name__ == '__main__':
    test_ipm_engine()
