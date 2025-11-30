"""
Image encryption utilities using AES-256
Implements encryption at rest for uploaded images
Requirements: 11.4
"""
import os
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

logger = logging.getLogger(__name__)

# Get encryption key from environment variable
# In production, this should be stored securely (e.g., AWS Secrets Manager, Azure Key Vault)
ENCRYPTION_KEY = os.environ.get('IMAGE_ENCRYPTION_KEY')

# Generate a default key for development if not set
if not ENCRYPTION_KEY:
    logger.warning("IMAGE_ENCRYPTION_KEY not set, using default key (NOT FOR PRODUCTION)")
    ENCRYPTION_KEY = b'0' * 32  # 32 bytes for AES-256
else:
    # Convert hex string to bytes if needed
    if isinstance(ENCRYPTION_KEY, str):
        ENCRYPTION_KEY = bytes.fromhex(ENCRYPTION_KEY)


def generate_encryption_key():
    """
    Generate a new AES-256 encryption key
    Returns 32-byte key as hex string
    """
    key = os.urandom(32)
    return key.hex()


def encrypt_image(image_path):
    """
    Encrypt an image file using AES-256
    
    Args:
        image_path: Path to the image file to encrypt
        
    Returns:
        Path to encrypted file (original_path + '.enc')
        
    Requirements: 11.4 - Image encryption at rest using AES-256
    """
    try:
        # Read the image file
        with open(image_path, 'rb') as f:
            plaintext = f.read()
        
        # Generate a random IV (Initialization Vector)
        iv = os.urandom(16)  # AES block size is 16 bytes
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Pad the plaintext to be a multiple of block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        
        # Encrypt the data
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Write encrypted file (IV + ciphertext)
        encrypted_path = image_path + '.enc'
        with open(encrypted_path, 'wb') as f:
            f.write(iv + ciphertext)
        
        # Delete original unencrypted file
        os.remove(image_path)
        
        logger.info(f"Image encrypted: {image_path} -> {encrypted_path}")
        return encrypted_path
        
    except Exception as e:
        logger.error(f"Error encrypting image {image_path}: {e}", exc_info=True)
        return None


def decrypt_image(encrypted_path):
    """
    Decrypt an encrypted image file
    
    Args:
        encrypted_path: Path to the encrypted file
        
    Returns:
        Decrypted image data as bytes
    """
    try:
        # Read the encrypted file
        with open(encrypted_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Extract IV (first 16 bytes) and ciphertext
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(ENCRYPTION_KEY),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt the data
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad the plaintext
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        logger.debug(f"Image decrypted: {encrypted_path}")
        return plaintext
        
    except Exception as e:
        logger.error(f"Error decrypting image {encrypted_path}: {e}", exc_info=True)
        return None


def serve_encrypted_image(encrypted_path):
    """
    Decrypt and serve an encrypted image
    
    Args:
        encrypted_path: Path to encrypted image file
        
    Returns:
        Tuple of (image_data, mimetype) or (None, None) on error
    """
    try:
        image_data = decrypt_image(encrypted_path)
        
        if not image_data:
            return None, None
        
        # Determine MIME type from original filename
        original_path = encrypted_path.replace('.enc', '')
        ext = os.path.splitext(original_path)[1].lower()
        
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        
        mimetype = mime_types.get(ext, 'image/jpeg')
        
        return image_data, mimetype
        
    except Exception as e:
        logger.error(f"Error serving encrypted image: {e}", exc_info=True)
        return None, None
