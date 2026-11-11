import os
import hashlib
import json
import struct
import time
from Crypto.Cipher import AES, ChaCha20_Poly1305
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from cryptography.fernet import Fernet
import bcrypt
import base64
import numpy as np
from PIL import Image

# ============== PASSWORD HASHING ==============
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ============== CLASSICAL ENCRYPTION ==============
def caesar_encrypt(text: str, shift: int = 7) -> str:
    """Caesar cipher encryption"""
    result = []
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + shift) % 26 + base))
        else:
            result.append(char)
    return ''.join(result)

def caesar_decrypt(text: str, shift: int = 7) -> str:
    """Caesar cipher decryption"""
    return caesar_encrypt(text, -shift)

def vigenere_encrypt(text: str, key: str = "KRIPTOGRAFI") -> str:
    """Vigenere cipher encryption"""
    result = []
    key_index = 0
    key = key.upper()
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shift = ord(key[key_index % len(key)]) - ord('A')
            result.append(chr((ord(char) - base + shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)

def vigenere_decrypt(text: str, key: str = "KRIPTOGRAFI") -> str:
    """Vigenere cipher decryption"""
    result = []
    key_index = 0
    key = key.upper()
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            shift = ord(key[key_index % len(key)]) - ord('A')
            result.append(chr((ord(char) - base - shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return ''.join(result)

# ============== MODERN ENCRYPTION (AES-256-CBC) ==============
def aes_encrypt(plaintext: str, key: bytes = None) -> dict:
    """AES-256-CBC encryption"""
    if key is None:
        key = get_random_bytes(32)
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext.encode('utf-8'), AES.block_size)
    ciphertext = cipher.encrypt(padded)
    return {
        'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
        'iv': base64.b64encode(iv).decode('utf-8'),
        'key': base64.b64encode(key).decode('utf-8')
    }

def aes_decrypt(ciphertext_b64: str, key_b64: str, iv_b64: str) -> str:
    """AES-256-CBC decryption"""
    ciphertext = base64.b64decode(ciphertext_b64)
    key = base64.b64decode(key_b64)
    iv = base64.b64decode(iv_b64)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ciphertext)
    return unpad(padded, AES.block_size).decode('utf-8')

# ============== SUPER ENCRYPTION (Classical + Modern) ==============
def super_encrypt(plaintext: str) -> dict:
    """Super encryption: Caesar -> Vigenere -> AES-256-CBC"""
    step1 = caesar_encrypt(plaintext)
    step2 = vigenere_encrypt(step1)
    step3 = aes_encrypt(step2)
    return {
        'encrypted': step3['ciphertext'],
        'iv': step3['iv'],
        'key': step3['key'],
        'method': 'Caesar(7) -> Vigenere(KRIPTOGRAFI) -> AES-256-CBC',
        'steps': {
            'original': plaintext,
            'after_caesar': step1,
            'after_vigenere': step2,
            'after_aes': step3['ciphertext']
        }
    }

def super_decrypt(encrypted_data: dict) -> str:
    """Decrypt super encryption: AES-256-CBC -> Vigenere -> Caesar"""
    step1 = aes_decrypt(encrypted_data['encrypted'], encrypted_data['key'], encrypted_data['iv'])
    step2 = vigenere_decrypt(step1)
    step3 = caesar_decrypt(step2)
    return step3

# ============== FILE ENCRYPTION (ChaCha20-Poly1305) ==============
def encrypt_file(file_data: bytes) -> dict:
    """Encrypt file using ChaCha20-Poly1305"""
    key = get_random_bytes(32)
    cipher = ChaCha20_Poly1305.new(key=key)
    ciphertext, tag = cipher.encrypt_and_digest(file_data)
    return {
        'ciphertext': ciphertext,
        'nonce': cipher.nonce,
        'tag': tag,
        'key': key
    }

def decrypt_file(ciphertext: bytes, key: bytes, nonce: bytes, tag: bytes) -> bytes:
    """Decrypt file using ChaCha20-Poly1305"""
    cipher = ChaCha20_Poly1305.new(key=key, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)

# ============== DATABASE FIELD ENCRYPTION (Fernet) ==============
_fernet_key = None

def get_fernet():
    global _fernet_key
    if _fernet_key is None:
        key_file = os.path.join(os.path.dirname(__file__), 'fernet.key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                _fernet_key = f.read()
        else:
            _fernet_key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(_fernet_key)
    return Fernet(_fernet_key)

def db_encrypt(data: str) -> str:
    """Encrypt data for database storage using Fernet"""
    f = get_fernet()
    return f.encrypt(data.encode('utf-8')).decode('utf-8')

def db_decrypt(encrypted_data: str) -> str:
    """Decrypt data from database using Fernet"""
    f = get_fernet()
    return f.decrypt(encrypted_data.encode('utf-8')).decode('utf-8')

# ============== STEGANOGRAPHY (LSB) ==============
def encode_image(image_path: str, message: str, output_path: str) -> bool:
    """Hide message in image using LSB steganography"""
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = np.array(img)
    
    # Add delimiter to know where message ends
    message += "###END###"
    binary_message = ''.join(format(ord(c), '08b') for c in message)
    
    if len(binary_message) > pixels.size:
        return False  # Message too long
    
    flat = pixels.flatten()
    for i, bit in enumerate(binary_message):
        flat[i] = (flat[i] & 0xFE) | int(bit)
    
    encoded = flat.reshape(pixels.shape)
    result = Image.fromarray(encoded.astype('uint8'))
    result.save(output_path)
    return True

def decode_image(image_path: str) -> str:
    """Extract hidden message from image using LSB steganography"""
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = np.array(img)
    flat = pixels.flatten()
    
    binary = ''
    message = ''
    for i in range(len(flat)):
        binary += str(flat[i] & 1)
        if len(binary) == 8:
            char = chr(int(binary, 2))
            message += char
            binary = ''
            if message.endswith("###END###"):
                return message[:-9]
    
    return message

# ============== BLOCKCHAIN ==============
class Block:
    def __init__(self, index, data, previous_hash, timestamp=None):
        self.index = index
        self.timestamp = timestamp or time.time()
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()
    
    def calculate_hash(self):
        block_string = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty=2):
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash

class Blockchain:
    def __init__(self):
        self.chain = []
        self.difficulty = 2
    
    def create_genesis_block(self):
        genesis = Block(0, "Genesis Block", "0")
        genesis.mine_block(self.difficulty)
        return genesis
    
    def get_latest_block(self):
        if not self.chain:
            return None
        return self.chain[-1]
    
    def add_block(self, data):
        latest = self.get_latest_block()
        if latest is None:
            genesis = self.create_genesis_block()
            self.chain.append(genesis)
            latest = genesis
        
        new_block = Block(len(self.chain), data, latest.hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)
        return new_block
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

# ============== DONGLE FUNCTIONS ==============
def get_dongle_status() -> dict:
    """Cari token pada root drive USB; tidak menerima salinan di folder aplikasi."""
    import string

    dongle_content = "KRIPTO-APP-AUTHORIZED-DONGLE-2024"
    for drive in string.ascii_uppercase:
        root = f"{drive}:\\"
        token_path = os.path.join(root, "kripto_dongle.key")
        try:
            if os.path.isfile(token_path):
                with open(token_path, "r", encoding="utf-8") as token_file:
                    if token_file.read().strip() == dongle_content:
                        return {"active": True, "drive": f"{drive}:", "message": f"Dongle terdeteksi di {drive}:"}
        except (PermissionError, OSError, UnicodeError):
            continue
    return {"active": False, "drive": None, "message": "Dongle USB tidak ditemukan. Pastikan USB terpasang dan file kripto_dongle.key berada di root USB."}


def check_dongle() -> bool:
    """True hanya jika token valid ditemukan pada drive USB."""
    return get_dongle_status()["active"]

def create_dongle_file(path: str = None) -> str:
    """Create a dongle token file (for setup/testing)"""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), 'kripto_dongle.key')
    with open(path, 'w') as f:
        f.write("KRIPTO-APP-AUTHORIZED-DONGLE-2024")
    return path
