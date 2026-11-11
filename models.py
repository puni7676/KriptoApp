from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Model pengguna dengan data autentikasi"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    face_encoding_data = db.Column(db.Text, nullable=True)  # JSON-encoded face encoding
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy='dynamic')
    files = db.relationship('FileRecord', backref='owner', lazy='dynamic')
    stego_images = db.relationship('StegoImage', backref='owner', lazy='dynamic')
    assets = db.relationship('EncryptedAsset', backref='owner', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class Message(db.Model):
    """Model pesan terenkripsi"""
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_encrypted = db.Column(db.Text, nullable=False)  # Fernet-encrypted JSON of super-encrypted data
    encryption_type = db.Column(db.String(100), default='Super Encryption (Caesar+Vigenere+AES-256-CBC)')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id} to {self.receiver_id}>'


class FileRecord(db.Model):
    """Model catatan file terenkripsi"""
    __tablename__ = 'file_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    encrypted_filename = db.Column(db.String(255), nullable=False)
    encryption_key_encrypted = db.Column(db.Text, nullable=False)  # Fernet-encrypted key+nonce+tag
    file_size = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<FileRecord {self.original_filename}>'


class StegoImage(db.Model):
    """Model gambar steganografi"""
    __tablename__ = 'stego_images'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_image = db.Column(db.String(255), nullable=False)
    stego_image = db.Column(db.String(255), nullable=False)
    message_length = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StegoImage {self.id}>'


class BlockchainBlock(db.Model):
    """Model blok blockchain di database"""
    __tablename__ = 'blockchain_blocks'

    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    data = db.Column(db.Text, nullable=False)
    previous_hash = db.Column(db.String(64), nullable=False)
    hash = db.Column(db.String(64), nullable=False)
    nonce = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Block #{self.index} hash={self.hash[:8]}...>'


class EncryptedAsset(db.Model):
    """Model aset yang diamankan oleh blockchain"""
    __tablename__ = 'encrypted_assets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    asset_name = db.Column(db.String(255), nullable=False)
    asset_data_encrypted = db.Column(db.Text, nullable=False)  # Fernet-encrypted asset data
    block_index = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Asset {self.asset_name}>'
