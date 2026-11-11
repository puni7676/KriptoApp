import os
import json
import uuid
import base64
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from models import db, FileRecord
from crypto_utils import encrypt_file, decrypt_file, db_encrypt, db_decrypt

files_bp = Blueprint('files', __name__)


def allowed_file(filename):
    """Periksa apakah ekstensi file diizinkan"""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', set())
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@files_bp.route('/files')
@login_required
def list_files():
    """Daftar file terenkripsi milik pengguna"""
    files = FileRecord.query.filter_by(user_id=current_user.id).order_by(FileRecord.timestamp.desc()).all()
    return render_template('files.html', files=files)


@files_bp.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload dan enkripsi file menggunakan ChaCha20-Poly1305"""
    if 'file' not in request.files:
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(url_for('files.list_files'))

    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih.', 'danger')
        return redirect(url_for('files.list_files'))

    if not allowed_file(file.filename):
        flash('Tipe file tidak diizinkan.', 'danger')
        return redirect(url_for('files.list_files'))

    try:
        # Read file data
        file_data = file.read()
        original_filename = file.filename
        file_size = len(file_data)

        # Encrypt file using ChaCha20-Poly1305
        result = encrypt_file(file_data)

        # Generate unique encrypted filename
        encrypted_filename = f"{uuid.uuid4().hex}.enc"
        encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], encrypted_filename)

        # Save encrypted file
        with open(encrypted_path, 'wb') as f:
            f.write(result['ciphertext'])

        # Encrypt the key metadata using Fernet for DB storage
        key_data = json.dumps({
            'key': base64.b64encode(result['key']).decode('utf-8'),
            'nonce': base64.b64encode(result['nonce']).decode('utf-8'),
            'tag': base64.b64encode(result['tag']).decode('utf-8')
        })
        encrypted_key_data = db_encrypt(key_data)

        # Save record to database
        record = FileRecord(
            user_id=current_user.id,
            original_filename=original_filename,
            encrypted_filename=encrypted_filename,
            encryption_key_encrypted=encrypted_key_data,
            file_size=file_size
        )
        db.session.add(record)
        db.session.commit()

        flash(f'File "{original_filename}" berhasil dienkripsi dengan ChaCha20-Poly1305!', 'success')

    except Exception as e:
        flash(f'Gagal mengenkripsi file: {str(e)}', 'danger')

    return redirect(url_for('files.list_files'))


@files_bp.route('/files/download/<int:file_id>')
@login_required
def download_file(file_id):
    """Dekripsi dan download file"""
    record = FileRecord.query.get_or_404(file_id)

    # Only the owner can download
    if record.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke file ini.', 'danger')
        return redirect(url_for('files.list_files'))

    try:
        # Read encrypted file
        encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], record.encrypted_filename)
        with open(encrypted_path, 'rb') as f:
            ciphertext = f.read()

        # Decrypt key metadata from DB
        key_json = db_decrypt(record.encryption_key_encrypted)
        key_data = json.loads(key_json)

        key = base64.b64decode(key_data['key'])
        nonce = base64.b64decode(key_data['nonce'])
        tag = base64.b64decode(key_data['tag'])

        # Decrypt file using ChaCha20-Poly1305
        decrypted_data = decrypt_file(ciphertext, key, nonce, tag)

        # Save to temp file and send
        import tempfile
        temp_path = os.path.join(tempfile.gettempdir(), record.original_filename)
        with open(temp_path, 'wb') as f:
            f.write(decrypted_data)

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=record.original_filename
        )

    except Exception as e:
        flash(f'Gagal mendekripsi file: {str(e)}', 'danger')
        return redirect(url_for('files.list_files'))


@files_bp.route('/files/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    """Hapus file terenkripsi"""
    record = FileRecord.query.get_or_404(file_id)

    if record.user_id != current_user.id:
        flash('Anda tidak memiliki akses ke file ini.', 'danger')
        return redirect(url_for('files.list_files'))

    try:
        # Delete encrypted file from disk
        encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], record.encrypted_filename)
        if os.path.exists(encrypted_path):
            os.remove(encrypted_path)

        # Delete record from database
        db.session.delete(record)
        db.session.commit()
        flash('File berhasil dihapus.', 'success')

    except Exception as e:
        flash(f'Gagal menghapus file: {str(e)}', 'danger')

    return redirect(url_for('files.list_files'))
