"""
Demo script to test history endpoints manually
Run this after starting the Flask app
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_history_endpoints():
    """Test the history endpoints with a real session"""
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("=" * 60)
    print("Testing History Endpoints")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_data = {
        'email': 'test@example.com',  # Use an existing user
        'password': 'testpass'
    }
    
    response = session.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✓ Login successful")
    else:
        print(f"✗ Login failed with status {response.status_code}")
        print("Please create a test user first or update the credentials")
        return
    
    # Step 2: Test GET /api/history
    print("\n2. Testing GET /api/history...")
    response = session.get(f"{BASE_URL}/api/history")
    
    if response.status_code == 200:
        history = response.json()
        print(f"✓ Retrieved {len(history)} scans")
        
        if history:
            print("\nFirst scan:")
            first_scan = history[0]
            print(f"  ID: {first_scan.get('id')}")
            print(f"  Date: {first_scan.get('date')}")
            print(f"  Pest: {first_scan.get('pest_identified')}")
            print(f"  Confidence: {first_scan.get('confidence')}%")
            print(f"  Severity: {first_scan.get('severity')}")
            
            # Step 3: Test GET /api/history/<scan_id>
            scan_id = first_scan['id']
            print(f"\n3. Testing GET /api/history/{scan_id}...")
            response = session.get(f"{BASE_URL}/api/history/{scan_id}")
            
            if response.status_code == 200:
                detail = response.json()
                print(f"✓ Retrieved detailed scan information")
                print(f"  Pest: {detail.get('pest_identified')}")
                print(f"  Scientific Name: {detail.get('pest_scientific')}")
                print(f"  Image Path: {detail.get('image_path')}")
                print(f"  Model Version: {detail.get('model_version')}")
                print(f"  Recommendations: {len(detail.get('recommendations', []))} found")
                
                if detail.get('metadata'):
                    print(f"  MongoDB Metadata: Present")
                    print(f"    Alternatives: {len(detail['metadata'].get('alternatives', []))}")
            else:
                print(f"✗ Failed to retrieve scan detail: {response.status_code}")
        else:
            print("  No scans found in history")
    else:
        print(f"✗ Failed to retrieve history: {response.status_code}")
    
    # Step 4: Test export as JSON
    print("\n4. Testing GET /api/export/scans?format=json...")
    response = session.get(f"{BASE_URL}/api/export/scans?format=json")
    
    if response.status_code == 200:
        print(f"✓ Export successful")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Content-Disposition: {response.headers.get('Content-Disposition')}")
        
        data = response.json()
        print(f"  Exported {len(data)} scans")
    else:
        print(f"✗ Export failed: {response.status_code}")
    
    # Step 5: Test export as CSV
    print("\n5. Testing GET /api/export/scans?format=csv...")
    response = session.get(f"{BASE_URL}/api/export/scans?format=csv")
    
    if response.status_code == 200:
        print(f"✓ CSV export successful")
        print(f"  Content-Type: {response.headers.get('Content-Type')}")
        print(f"  Content-Disposition: {response.headers.get('Content-Disposition')}")
        
        # Show first few lines of CSV
        csv_lines = response.text.split('\n')[:3]
        print(f"  First 3 lines:")
        for line in csv_lines:
            print(f"    {line[:80]}...")
    else:
        print(f"✗ CSV export failed: {response.status_code}")
    
    # Step 6: Test invalid format
    print("\n6. Testing invalid format parameter...")
    response = session.get(f"{BASE_URL}/api/export/scans?format=xml")
    
    if response.status_code == 400:
        error = response.json()
        print(f"✓ Correctly rejected invalid format")
        print(f"  Error message: {error.get('error')}")
    else:
        print(f"✗ Unexpected response: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        test_history_endpoints()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Flask app")
        print("Please make sure the Flask app is running on http://localhost:5001")
    except Exception as e:
        print(f"Error: {e}")
