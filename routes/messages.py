import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Message
from crypto_utils import super_encrypt, super_decrypt, db_encrypt, db_decrypt, caesar_encrypt, vigenere_encrypt

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/messages')
@login_required
def list_messages():
    """Daftar semua pesan (terkirim dan diterima)"""
    received = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.timestamp.desc()).all()
    sent = Message.query.filter_by(sender_id=current_user.id).order_by(Message.timestamp.desc()).all()
    users = User.query.filter(User.id != current_user.id).all()

    # Decrypt messages for display
    decrypted_received = []
    for msg in received:
        try:
            encrypted_json = db_decrypt(msg.content_encrypted)
            encrypted_data = json.loads(encrypted_json)
            plaintext = super_decrypt(encrypted_data)
            decrypted_received.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'content': plaintext,
                'encryption_type': msg.encryption_type,
                'timestamp': msg.timestamp
            })
        except Exception as e:
            decrypted_received.append({
                'id': msg.id,
                'sender': msg.sender.username,
                'content': f'[Gagal mendekripsi: {str(e)}]',
                'encryption_type': msg.encryption_type,
                'timestamp': msg.timestamp
            })

    decrypted_sent = []
    for msg in sent:
        try:
            encrypted_json = db_decrypt(msg.content_encrypted)
            encrypted_data = json.loads(encrypted_json)
            plaintext = super_decrypt(encrypted_data)
            decrypted_sent.append({
                'id': msg.id,
                'receiver': msg.receiver.username,
                'content': plaintext,
                'encryption_type': msg.encryption_type,
                'timestamp': msg.timestamp
            })
        except Exception as e:
            decrypted_sent.append({
                'id': msg.id,
                'receiver': msg.receiver.username,
                'content': f'[Gagal mendekripsi: {str(e)}]',
                'encryption_type': msg.encryption_type,
                'timestamp': msg.timestamp
            })

    return render_template('messages.html',
                           received=decrypted_received,
                           sent=decrypted_sent,
                           users=users)


@messages_bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Kirim pesan terenkripsi (super encryption)"""
    receiver_id = request.form.get('receiver_id', type=int)
    content = request.form.get('content', '').strip()

    if not receiver_id or not content:
        flash('Penerima dan isi pesan harus diisi.', 'danger')
        return redirect(url_for('messages.list_messages'))

    receiver = User.query.get(receiver_id)
    if not receiver:
        flash('Penerima tidak ditemukan.', 'danger')
        return redirect(url_for('messages.list_messages'))

    if receiver.id == current_user.id:
        flash('Tidak dapat mengirim pesan ke diri sendiri.', 'warning')
        return redirect(url_for('messages.list_messages'))

    # Super Encryption: Caesar -> Vigenere -> AES-256-CBC
    encrypted_data = super_encrypt(content)

    # Store encrypted data as Fernet-encrypted JSON in database
    encrypted_json = json.dumps({
        'encrypted': encrypted_data['encrypted'],
        'iv': encrypted_data['iv'],
        'key': encrypted_data['key']
    })
    db_encrypted = db_encrypt(encrypted_json)

    msg = Message(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content_encrypted=db_encrypted,
        encryption_type=encrypted_data['method']
    )
    db.session.add(msg)
    db.session.commit()

    flash('Pesan berhasil dikirim dengan Super Encryption!', 'success')
    return redirect(url_for('messages.list_messages'))


@messages_bp.route('/messages/<int:msg_id>')
@login_required
def view_message(msg_id):
    """Lihat detail pesan beserta langkah enkripsi"""
    msg = Message.query.get_or_404(msg_id)

    # Only sender or receiver can view
    if msg.sender_id != current_user.id and msg.receiver_id != current_user.id:
        flash('Anda tidak memiliki akses ke pesan ini.', 'danger')
        return redirect(url_for('messages.list_messages'))

    try:
        # Decrypt from DB (Fernet)
        encrypted_json = db_decrypt(msg.content_encrypted)
        encrypted_data = json.loads(encrypted_json)

        # Full decryption to get plaintext
        plaintext = super_decrypt(encrypted_data)

        # Show encryption steps for educational purpose
        step1_caesar = caesar_encrypt(plaintext)
        step2_vigenere = vigenere_encrypt(step1_caesar)

        steps = {
            'original': plaintext,
            'after_caesar': step1_caesar,
            'after_vigenere': step2_vigenere,
            'after_aes': encrypted_data['encrypted'],
            'db_stored': msg.content_encrypted[:80] + '...' if len(msg.content_encrypted) > 80 else msg.content_encrypted
        }

        detail = {
            'id': msg.id,
            'sender': msg.sender.username,
            'receiver': msg.receiver.username,
            'plaintext': plaintext,
            'encryption_type': msg.encryption_type,
            'timestamp': msg.timestamp,
            'steps': steps,
            'iv': encrypted_data['iv'],
            'aes_key': encrypted_data['key']
        }

        return render_template('message_detail.html', msg=detail)

    except Exception as e:
        flash(f'Gagal mendekripsi pesan: {str(e)}', 'danger')
        return redirect(url_for('messages.list_messages'))
