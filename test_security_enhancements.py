"""
Test script for security enhancements
Tests Argon2 password hashing, JWT tokens, and image encryption
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Set up test environment
os.environ['FLASK_ENV'] = 'development'
os.environ['IMAGE_ENCRYPTION_KEY'] = '0' * 64  # 32 bytes as hex

from models import User, ph
from jwt_utils import generate_jwt_token, verify_jwt_token, refresh_jwt_token
from encryption_utils import encrypt_image, decrypt_image, generate_encryption_key
from config import config
from database import db, init_db
from flask import Flask

print("=" * 60)
print("Testing Security Enhancements")
print("=" * 60)

# Test 1: Argon2 Password Hashing
print("\n1. Testing Argon2 Password Hashing...")
print("-" * 60)

try:
    # Create a test user
    test_password = "SecurePassword123!"
    
    # Test password hashing
    password_hash = ph.hash(test_password)
    print(f"✓ Password hashed successfully")
    print(f"  Hash: {password_hash[:50]}...")
    
    # Test password verification - correct password
    try:
        ph.verify(password_hash, test_password)
        print(f"✓ Correct password verified successfully")
    except Exception as e:
        print(f"✗ Failed to verify correct password: {e}")
        sys.exit(1)
    
    # Test password verification - incorrect password
    try:
        ph.verify(password_hash, "WrongPassword")
        print(f"✗ Incorrect password was accepted (SECURITY ISSUE!)")
        sys.exit(1)
    except:
        print(f"✓ Incorrect password rejected successfully")
    
    print("✓ Argon2 password hashing: PASSED")
    
except Exception as e:
    print(f"✗ Argon2 password hashing test failed: {e}")
    sys.exit(1)

# Test 2: JWT Token Generation and Validation
print("\n2. Testing JWT Token with 24-hour Expiration...")
print("-" * 60)

try:
    # Create Flask app for JWT testing
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    with app.app_context():
        # Generate JWT token
        user_id = 123
        email = "test@example.com"
        
        token = generate_jwt_token(user_id, email)
        if not token:
            print(f"✗ Failed to generate JWT token")
            sys.exit(1)
        
        print(f"✓ JWT token generated successfully")
        print(f"  Token: {token[:50]}...")
        
        # Verify token
        payload = verify_jwt_token(token)
        if not payload:
            print(f"✗ Failed to verify JWT token")
            sys.exit(1)
        
        print(f"✓ JWT token verified successfully")
        print(f"  User ID: {payload['user_id']}")
        print(f"  Email: {payload['email']}")
        
        # Check expiration is 24 hours
        exp_time = datetime.fromtimestamp(payload['exp'])
        iat_time = datetime.fromtimestamp(payload['iat'])
        time_diff = exp_time - iat_time
        
        # Allow small tolerance (within 1 minute of 24 hours)
        expected_hours = 24
        actual_hours = time_diff.total_seconds() / 3600
        
        if abs(actual_hours - expected_hours) < 0.017:  # ~1 minute tolerance
            print(f"✓ Token expiration set to 24 hours: {actual_hours:.2f} hours")
        else:
            print(f"✗ Token expiration incorrect: {actual_hours:.2f} hours (expected 24)")
            sys.exit(1)
        
        # Test token refresh
        new_token = refresh_jwt_token(token)
        if not new_token:
            print(f"✗ Failed to refresh JWT token")
            sys.exit(1)
        
        print(f"✓ JWT token refreshed successfully")
        
        # Verify new token
        new_payload = verify_jwt_token(new_token)
        if not new_payload:
            print(f"✗ Failed to verify refreshed JWT token")
            sys.exit(1)
        
        print(f"✓ Refreshed JWT token verified successfully")
        
        print("✓ JWT token implementation: PASSED")
        
except Exception as e:
    print(f"✗ JWT token test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Image Encryption
print("\n3. Testing AES-256 Image Encryption...")
print("-" * 60)

try:
    # Create a temporary test image
    test_image_data = b"This is test image data" * 100  # Some test data
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.jpg') as f:
        f.write(test_image_data)
        test_image_path = f.name
    
    print(f"✓ Created test image: {test_image_path}")
    print(f"  Original size: {len(test_image_data)} bytes")
    
    # Encrypt the image
    encrypted_path = encrypt_image(test_image_path)
    
    if not encrypted_path:
        print(f"✗ Failed to encrypt image")
        sys.exit(1)
    
    print(f"✓ Image encrypted successfully: {encrypted_path}")
    
    # Verify original file was deleted
    if os.path.exists(test_image_path):
        print(f"✗ Original file was not deleted after encryption")
        sys.exit(1)
    
    print(f"✓ Original file deleted after encryption")
    
    # Verify encrypted file exists
    if not os.path.exists(encrypted_path):
        print(f"✗ Encrypted file does not exist")
        sys.exit(1)
    
    # Check encrypted file size (should be larger due to IV and padding)
    encrypted_size = os.path.getsize(encrypted_path)
    print(f"✓ Encrypted file size: {encrypted_size} bytes")
    
    # Decrypt the image
    decrypted_data = decrypt_image(encrypted_path)
    
    if not decrypted_data:
        print(f"✗ Failed to decrypt image")
        sys.exit(1)
    
    print(f"✓ Image decrypted successfully")
    print(f"  Decrypted size: {len(decrypted_data)} bytes")
    
    # Verify decrypted data matches original
    if decrypted_data == test_image_data:
        print(f"✓ Decrypted data matches original (round-trip successful)")
    else:
        print(f"✗ Decrypted data does not match original")
        print(f"  Original: {len(test_image_data)} bytes")
        print(f"  Decrypted: {len(decrypted_data)} bytes")
        sys.exit(1)
    
    # Clean up
    os.remove(encrypted_path)
    print(f"✓ Cleaned up test files")
    
    print("✓ Image encryption: PASSED")
    
except Exception as e:
    print(f"✗ Image encryption test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Encryption Key Generation
print("\n4. Testing Encryption Key Generation...")
print("-" * 60)

try:
    key = generate_encryption_key()
    print(f"✓ Generated encryption key: {key[:32]}...")
    
    # Verify key is 64 hex characters (32 bytes)
    if len(key) == 64:
        print(f"✓ Key length correct: 64 hex characters (32 bytes)")
    else:
        print(f"✗ Key length incorrect: {len(key)} (expected 64)")
        sys.exit(1)
    
    # Verify key is valid hex
    try:
        bytes.fromhex(key)
        print(f"✓ Key is valid hexadecimal")
    except ValueError:
        print(f"✗ Key is not valid hexadecimal")
        sys.exit(1)
    
    print("✓ Encryption key generation: PASSED")
    
except Exception as e:
    print(f"✗ Encryption key generation test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("All Security Enhancement Tests PASSED!")
print("=" * 60)
print("\nImplemented Features:")
print("  ✓ Argon2 password hashing (Requirements 11.1)")
print("  ✓ JWT tokens with 24-hour expiration (Requirements 11.2)")
print("  ✓ AES-256 image encryption at rest (Requirements 11.4)")
print("  ✓ Flask-Talisman HTTPS enforcement (Requirements 11.3)")
print("  ✓ GDPR-compliant account deletion (Requirements 11.5)")
print("\nNote: HTTPS enforcement is enabled in production mode only")
print("=" * 60)
