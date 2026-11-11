import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, StegoImage
from crypto_utils import encode_image, decode_image

stego_bp = Blueprint('stego', __name__)


def allowed_image(filename):
    """Periksa apakah file adalah gambar yang didukung untuk steganografi"""
    allowed = {'png', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed


@stego_bp.route('/stego')
@login_required
def stego_page():
    """Halaman steganografi"""
    images = StegoImage.query.filter_by(user_id=current_user.id).order_by(StegoImage.timestamp.desc()).all()
    return render_template('stego.html', images=images)


@stego_bp.route('/stego/encode', methods=['POST'])
@login_required
def encode():
    """Encode pesan tersembunyi ke dalam gambar (LSB Steganography)"""
    if 'image' not in request.files:
        flash('Tidak ada gambar yang dipilih.', 'danger')
        return redirect(url_for('stego.stego_page'))

    image_file = request.files['image']
    message = request.form.get('message', '').strip()

    if image_file.filename == '':
        flash('Tidak ada gambar yang dipilih.', 'danger')
        return redirect(url_for('stego.stego_page'))

    if not message:
        flash('Pesan tidak boleh kosong.', 'danger')
        return redirect(url_for('stego.stego_page'))

    if not allowed_image(image_file.filename):
        flash('Hanya file PNG atau BMP yang didukung untuk steganografi.', 'danger')
        return redirect(url_for('stego.stego_page'))

    try:
        # Save original image
        original_name = f"orig_{uuid.uuid4().hex}.png"
        original_path = os.path.join(current_app.config['STEGO_FOLDER'], original_name)
        image_file.save(original_path)

        # Encode message into image
        stego_name = f"stego_{uuid.uuid4().hex}.png"
        stego_path = os.path.join(current_app.config['STEGO_FOLDER'], stego_name)

        success = encode_image(original_path, message, stego_path)

        if success:
            # Save record to database
            record = StegoImage(
                user_id=current_user.id,
                original_image=original_name,
                stego_image=stego_name,
                message_length=len(message)
            )
            db.session.add(record)
            db.session.commit()

            flash('Pesan berhasil disembunyikan dalam gambar menggunakan LSB Steganography!', 'success')
        else:
            flash('Pesan terlalu panjang untuk gambar ini. Gunakan gambar yang lebih besar.', 'danger')
            # Clean up
            if os.path.exists(original_path):
                os.remove(original_path)

    except Exception as e:
        flash(f'Gagal menyembunyikan pesan: {str(e)}', 'danger')

    return redirect(url_for('stego.stego_page'))


@stego_bp.route('/stego/decode', methods=['POST'])
@login_required
def decode():
    """Decode pesan tersembunyi dari gambar steganografi"""
    if 'stego_image' not in request.files:
        flash('Tidak ada gambar yang dipilih.', 'danger')
        return redirect(url_for('stego.stego_page'))

    image_file = request.files['stego_image']

    if image_file.filename == '':
        flash('Tidak ada gambar yang dipilih.', 'danger')
        return redirect(url_for('stego.stego_page'))

    try:
        # Save temporarily
        temp_name = f"decode_{uuid.uuid4().hex}.png"
        temp_path = os.path.join(current_app.config['STEGO_FOLDER'], temp_name)
        image_file.save(temp_path)

        # Decode the message
        hidden_message = decode_image(temp_path)

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if hidden_message:
            flash(f'Pesan tersembunyi ditemukan!', 'success')
            return render_template('stego.html',
                                   images=StegoImage.query.filter_by(user_id=current_user.id).order_by(StegoImage.timestamp.desc()).all(),
                                   decoded_message=hidden_message)
        else:
            flash('Tidak ada pesan tersembunyi yang ditemukan.', 'warning')

    except Exception as e:
        flash(f'Gagal membaca pesan: {str(e)}', 'danger')

    return redirect(url_for('stego.stego_page'))


@stego_bp.route('/stego/download/<filename>')
@login_required
def download_stego(filename):
    """Download gambar steganografi"""
    # Verify the file belongs to the current user
    record = StegoImage.query.filter(
        (StegoImage.stego_image == filename) | (StegoImage.original_image == filename),
        StegoImage.user_id == current_user.id
    ).first()

    if not record:
        flash('File tidak ditemukan.', 'danger')
        return redirect(url_for('stego.stego_page'))

    file_path = os.path.join(current_app.config['STEGO_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        flash('File tidak ditemukan di server.', 'danger')
        return redirect(url_for('stego.stego_page'))
