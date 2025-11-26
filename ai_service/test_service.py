"""
Simple test script to verify AI service functionality
"""
import requests
import io
from PIL import Image
import numpy as np


def create_test_image():
    """Create a simple test image"""
    # Create a 224x224 RGB image with random noise
    img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(img_array)
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


def test_health_check():
    """Test health check endpoint"""
    print("Testing health check endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_detect_endpoint():
    """Test pest detection endpoint"""
    print("\nTesting pest detection endpoint...")
    try:
        # Create test image
        img_bytes = create_test_image()
        
        # Send request
        files = {'image': ('test.jpg', img_bytes, 'image/jpeg')}
        response = requests.post("http://localhost:8000/ai/detect", files=files)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Pest detected: {result['pest_label']}")
            print(f"Scientific name: {result['scientific_name']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"Processing time: {result['processing_time_ms']:.2f}ms")
            print(f"Fallback used: {result['fallback_used']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("AGBOT AI Service Test Suite")
    print("=" * 60)
    
    # Test health check
    health_ok = test_health_check()
    
    # Test detection
    detect_ok = test_detect_endpoint()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"  Health Check: {'✓ PASS' if health_ok else '✗ FAIL'}")
    print(f"  Detection:    {'✓ PASS' if detect_ok else '✗ FAIL'}")
    print("=" * 60)
    
    if health_ok and detect_ok:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed. Check the service logs.")
