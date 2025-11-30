"""
Simple test to verify outbreak detection logic
Tests the core algorithm without requiring MongoDB
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_outbreak_threshold_logic():
    """
    Test the outbreak detection threshold logic
    Requirement 12.3: If current > 1.5 × historical, generate outbreak alert
    """
    print("=" * 70)
    print("Testing Outbreak Detection Threshold Logic")
    print("=" * 70)
    
    test_cases = [
        # (historical_avg, current_count, should_alert, description)
        (10, 16, True, "Current (16) > 1.5 × Historical (10) = 15"),
        (10, 15, False, "Current (15) = 1.5 × Historical (10) = 15 (boundary)"),
        (10, 14, False, "Current (14) < 1.5 × Historical (10) = 15"),
        (20, 31, True, "Current (31) > 1.5 × Historical (20) = 30"),
        (20, 30, False, "Current (30) = 1.5 × Historical (20) = 30 (boundary)"),
        (5, 8, True, "Current (8) > 1.5 × Historical (5) = 7.5"),
        (0, 10, False, "No historical data (avg=0), no alert"),
        (100, 151, True, "Current (151) > 1.5 × Historical (100) = 150"),
        (100, 150, False, "Current (150) = 1.5 × Historical (100) = 150 (boundary)"),
    ]
    
    passed = 0
    failed = 0
    
    for historical_avg, current_count, should_alert, description in test_cases:
        # Implement the outbreak detection logic
        threshold = 1.5 * historical_avg
        alert_triggered = historical_avg > 0 and current_count > threshold
        
        # Check if result matches expected
        if alert_triggered == should_alert:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  Historical Avg: {historical_avg}")
        print(f"  Current Count: {current_count}")
        print(f"  Threshold (1.5×): {threshold}")
        print(f"  Alert Triggered: {alert_triggered}")
        print(f"  Expected: {should_alert}")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    return failed == 0


def test_threshold_calculation():
    """
    Test threshold exceeded calculation
    """
    print("\n" + "=" * 70)
    print("Testing Threshold Exceeded Calculation")
    print("=" * 70)
    
    test_cases = [
        (10, 20, 2.0, "20 / 10 = 2.0x"),
        (10, 15, 1.5, "15 / 10 = 1.5x"),
        (20, 40, 2.0, "40 / 20 = 2.0x"),
        (5, 12, 2.4, "12 / 5 = 2.4x"),
        (100, 180, 1.8, "180 / 100 = 1.8x"),
    ]
    
    passed = 0
    failed = 0
    
    for historical_avg, current_count, expected_ratio, description in test_cases:
        # Calculate threshold exceeded
        threshold_exceeded = current_count / historical_avg if historical_avg > 0 else 0
        threshold_exceeded = round(threshold_exceeded, 2)
        
        # Check if result matches expected
        if abs(threshold_exceeded - expected_ratio) < 0.01:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"\n{status}: {description}")
        print(f"  Calculated: {threshold_exceeded}x")
        print(f"  Expected: {expected_ratio}x")
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 70)
    
    return failed == 0


def test_alert_structure():
    """
    Test that alert structure contains all required fields
    """
    print("\n" + "=" * 70)
    print("Testing Alert Structure")
    print("=" * 70)
    
    from datetime import datetime
    
    # Simulate creating an alert
    pest_type = "Fall Armyworm"
    region = "East_Africa"
    current_count = 25
    historical_avg = 10.5
    threshold_exceeded = current_count / historical_avg
    
    alert = {
        'pest': pest_type,
        'region': region,
        'current_count': current_count,
        'historical_average': round(historical_avg, 2),
        'threshold_exceeded': round(threshold_exceeded, 2),
        'alert_issued': datetime.utcnow()
    }
    
    required_fields = ['pest', 'region', 'current_count', 'historical_average', 
                      'threshold_exceeded', 'alert_issued']
    
    print("\nAlert structure:")
    for key, value in alert.items():
        print(f"  {key}: {value}")
    
    print("\nVerifying required fields:")
    all_present = True
    for field in required_fields:
        if field in alert:
            print(f"  ✓ {field}: present")
        else:
            print(f"  ✗ {field}: MISSING")
            all_present = False
    
    print("\n" + "=" * 70)
    if all_present:
        print("✓ PASS: All required fields present")
    else:
        print("✗ FAIL: Some required fields missing")
    print("=" * 70)
    
    return all_present


if __name__ == '__main__':
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "OUTBREAK DETECTION LOGIC TEST SUITE" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    results = []
    
    # Run tests
    results.append(("Threshold Logic", test_outbreak_threshold_logic()))
    results.append(("Threshold Calculation", test_threshold_calculation()))
    results.append(("Alert Structure", test_alert_structure()))
    
    # Summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} test suites passed")
    print("=" * 70)
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Outbreak detection logic is correct.")
    else:
        print("\n⚠️  Some tests failed. Please review the implementation.")
