import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Konfigurasi utama aplikasi Kripto"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kripto-app-super-secret-key-2024-TA'
    WTF_CSRF_ENABLED = True

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'kripto.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload folders
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    ENCRYPTED_FOLDER = os.path.join(basedir, 'uploads', 'encrypted')
    STEGO_FOLDER = os.path.join(basedir, 'uploads', 'stego')
    FACES_FOLDER = os.path.join(basedir, 'uploads', 'faces')

    # Max upload size: 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Dongle
    DONGLE_TOKEN = "kripto_dongle.key"
    DONGLE_CONTENT = "KRIPTO-APP-AUTHORIZED-DONGLE-2024"

    # Encryption defaults
    CAESAR_SHIFT = 7
    VIGENERE_KEY = "KRIPTOGRAFI"
    BLOCKCHAIN_DIFFICULTY = 2

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'csv'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'bmp'}  # Steganography needs lossless formats
