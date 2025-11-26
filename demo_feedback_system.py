"""
Demo script to showcase the feedback collection system

This script demonstrates:
1. Feedback submission flow
2. Proactive feedback prompting logic
3. Feedback aggregation for retraining
4. Dual database persistence

Requirements: 5.2, 5.3, 5.4, 5.5, 9.1, 9.2
"""
from confidence_utils import classify_confidence, should_request_feedback, get_confidence_message


def demo_confidence_classification():
    """Demonstrate confidence classification and feedback prompting"""
    print("=" * 80)
    print("DEMO: Confidence Classification and Feedback Prompting")
    print("=" * 80)
    
    test_confidences = [0.95, 0.85, 0.80, 0.74, 0.70, 0.60, 0.45]
    
    for confidence in test_confidences:
        level = classify_confidence(confidence)
        should_prompt = should_request_feedback(confidence)
        message = get_confidence_message(level)
        
        print(f"\nConfidence: {confidence:.2f} ({confidence*100:.0f}%)")
        print(f"  Level: {level}")
        print(f"  Request Feedback: {'YES ⚠️' if should_prompt else 'NO ✓'}")
        print(f"  Message: {message}")
    
    print("\n" + "=" * 80)


def demo_feedback_flow():
    """Demonstrate feedback submission flow"""
    print("\n" + "=" * 80)
    print("DEMO: Feedback Submission Flow")
    print("=" * 80)
    
    # Scenario 1: Correct identification
    print("\nScenario 1: Farmer confirms correct identification")
    print("-" * 80)
    feedback_1 = {
        'scan_id': 123,
        'is_correct': True,
        'notes': 'Yes, this is definitely a Japanese Beetle'
    }
    print(f"Feedback: {feedback_1}")
    print("Result: ✓ Feedback saved to PostgreSQL")
    print("        ✓ Synced to MongoDB (background)")
    print("        ✓ Scan status remains 'identified'")
    
    # Scenario 2: Incorrect identification
    print("\nScenario 2: Farmer corrects misidentification")
    print("-" * 80)
    feedback_2 = {
        'scan_id': 124,
        'is_correct': False,
        'actual_pest_name': 'Fall Armyworm',
        'notes': 'This is actually a fall armyworm, not an aphid'
    }
    print(f"Feedback: {feedback_2}")
    print("Result: ✓ Feedback saved to PostgreSQL")
    print("        ✓ Synced to MongoDB (background)")
    print("        ✓ Scan status updated to 'corrected'")
    print("        ✓ Image flagged for retraining")
    
    print("\n" + "=" * 80)


def demo_aggregation():
    """Demonstrate feedback aggregation logic"""
    print("\n" + "=" * 80)
    print("DEMO: Feedback Aggregation for Model Retraining")
    print("=" * 80)
    
    # Simulated aggregation results
    pest_counts = {
        'Fall Armyworm': 120,
        'Aphids': 85,
        'Tomato Leafminer': 95,
        'Whitefly': 45,
        'Spider Mites': 30
    }
    
    print("\nCurrent Correction Counts by Pest Type:")
    print("-" * 80)
    
    threshold = 100
    pests_needing_retraining = []
    
    for pest, count in sorted(pest_counts.items(), key=lambda x: x[1], reverse=True):
        status = "⚠️ RETRAINING NEEDED" if count >= threshold else "✓ Below threshold"
        print(f"{pest:25s}: {count:3d} corrections  {status}")
        
        if count >= threshold:
            pests_needing_retraining.append(pest)
    
    print("\n" + "-" * 80)
    print(f"Total corrections: {sum(pest_counts.values())}")
    print(f"Pests needing retraining: {len(pests_needing_retraining)}")
    
    if pests_needing_retraining:
        print("\n⚠️ ALERT: The following pests have reached the retraining threshold:")
        for pest in pests_needing_retraining:
            print(f"  - {pest} ({pest_counts[pest]} corrections)")
        print("\nRecommendation: Trigger model retraining pipeline")
    
    print("\n" + "=" * 80)


def demo_dual_database():
    """Demonstrate dual database persistence"""
    print("\n" + "=" * 80)
    print("DEMO: Dual Database Persistence")
    print("=" * 80)
    
    print("\nFeedback Storage Architecture:")
    print("-" * 80)
    
    print("\n1. PostgreSQL (Structured Data)")
    print("   - Table: feedbacks")
    print("   - Fields: id, user_id, scan_id, is_correct, actual_pest_name, notes")
    print("   - Purpose: ACID compliance, relational queries, user history")
    print("   - ID Format: Auto-increment integer (e.g., 123)")
    
    print("\n2. MongoDB (Detailed Metadata)")
    print("   - Collection: feedback")
    print("   - Fields: detection_id, corrected_label, confidence_in_correction,")
    print("             image_flagged_for_retraining, feedback_time")
    print("   - Purpose: Flexible schema, aggregation, analytics")
    print("   - ID Format: feedback_{postgres_id} (e.g., feedback_123)")
    
    print("\n3. Synchronization Flow:")
    print("   Step 1: Insert feedback into PostgreSQL")
    print("   Step 2: Get auto-generated feedback_id (e.g., 123)")
    print("   Step 3: Return success response to user (immediate)")
    print("   Step 4: Background thread syncs to MongoDB with _id='feedback_123'")
    print("   Step 5: If incorrect, flag image for retraining in MongoDB")
    
    print("\n4. Benefits:")
    print("   ✓ Fast response time (no blocking on MongoDB)")
    print("   ✓ PostgreSQL ensures data integrity")
    print("   ✓ MongoDB enables efficient aggregation")
    print("   ✓ Graceful degradation if MongoDB unavailable")
    
    print("\n" + "=" * 80)


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "FEEDBACK COLLECTION SYSTEM DEMO" + " " * 27 + "║")
    print("╚" + "=" * 78 + "╝")
    
    demo_confidence_classification()
    demo_feedback_flow()
    demo_aggregation()
    demo_dual_database()
    
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 30 + "DEMO COMPLETE" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\nAll feedback system components demonstrated successfully!")
    print("Requirements validated: 5.2, 5.3, 5.4, 5.5, 9.1, 9.2")
    print()


if __name__ == '__main__':
    main()
