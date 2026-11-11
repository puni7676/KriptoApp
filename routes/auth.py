import json
import base64
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from crypto_utils import hash_password, verify_password, check_dongle, get_dongle_status, create_dongle_file

auth_bp = Blueprint('auth', __name__)

# MediaPipe mendeteksi lokasi wajah; OpenCV LBPH membandingkan wajah.
# Keduanya tersedia sebagai wheel Windows sehingga tidak membutuhkan dlib.
FACE_RECOGNITION_AVAILABLE = False
try:
    from face_utils import encode_face, extract_face, compare_faces
    FACE_RECOGNITION_AVAILABLE = True
except (ImportError, AttributeError):
    pass


@auth_bp.before_app_request
def check_dongle_middleware():
    """Periksa keberadaan dongle sebelum setiap request"""
    # Allow these endpoints without dongle
    allowed_endpoints = [
        'auth.dongle_required', 'auth.create_dongle_page',
        'auth.login', 'auth.register', 'auth.verify_face', 'auth.dongle_status',
        'static', None
    ]
    if request.endpoint in allowed_endpoints:
        return None

    if not check_dongle():
        if request.endpoint and request.endpoint != 'auth.dongle_required':
            return redirect(url_for('auth.dongle_required'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username dan password harus diisi.', 'danger')
            return render_template('login.html', face_available=FACE_RECOGNITION_AVAILABLE)

        user = User.query.filter_by(username=username).first()

        if user and verify_password(password, user.password_hash):
            login_user(user)
            flash(f'Selamat datang, {user.username}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Username atau password salah.', 'danger')

    return render_template('login.html', face_available=FACE_RECOGNITION_AVAILABLE)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman registrasi"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        face_data = request.form.get('face_data', '')

        if not username or not password:
            flash('Username dan password harus diisi.', 'danger')
            return render_template('register.html', face_available=FACE_RECOGNITION_AVAILABLE)

        if password != confirm_password:
            flash('Password tidak cocok.', 'danger')
            return render_template('register.html', face_available=FACE_RECOGNITION_AVAILABLE)

        if len(password) < 6:
            flash('Password minimal 6 karakter.', 'danger')
            return render_template('register.html', face_available=FACE_RECOGNITION_AVAILABLE)

        if User.query.filter_by(username=username).first():
            flash('Username sudah digunakan.', 'danger')
            return render_template('register.html', face_available=FACE_RECOGNITION_AVAILABLE)

        # Hash password with bcrypt
        hashed = hash_password(password)

        # Simpan potongan wajah ternormalisasi jika pengguna mengambil foto.
        face_encoding_json = None
        if face_data and FACE_RECOGNITION_AVAILABLE:
            try:
                face_encoding_json = encode_face(face_data)
            except Exception as e:
                flash(f'Gagal memproses wajah: {str(e)}. Akun tetap dibuat tanpa biometrik.', 'warning')

        user = User(
            username=username,
            password_hash=hashed,
            face_encoding_data=face_encoding_json
        )
        db.session.add(user)
        db.session.commit()

        flash('Registrasi berhasil! Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html', face_available=FACE_RECOGNITION_AVAILABLE)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout pengguna"""
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/verify-face', methods=['POST'])
def verify_face():
    """AJAX endpoint untuk verifikasi wajah via webcam."""
    if not FACE_RECOGNITION_AVAILABLE:
        return jsonify({'success': False, 'message': 'Modul MediaPipe/OpenCV belum terpasang.'}), 503

    try:
        data = request.get_json(silent=True) or {}
        image_data_url = data.get('image', '')
        if not image_data_url:
            return jsonify({'success': False, 'message': 'Tidak ada data gambar.'}), 400

        captured_face = extract_face(image_data_url)
        users_with_face = User.query.filter(User.face_encoding_data.isnot(None)).all()
        if not users_with_face:
            return jsonify({'success': False, 'message': 'Belum ada pengguna yang mendaftarkan wajah.'})

        best_user = None
        best_confidence = float('inf')
        for user in users_with_face:
            try:
                confidence = compare_faces(user.face_encoding_data, captured_face)
                if confidence < best_confidence:
                    best_confidence = confidence
                    best_user = user
            except Exception:
                continue

        # LBPH confidence is a distance score: lower is a closer match.
        # Threshold 65 is a conservative starting point and may need tuning.
        if best_user is not None and best_confidence <= 65.0:
            login_user(best_user)
            return jsonify({
                'success': True,
                'message': f'Selamat datang, {best_user.username}!',
                'redirect': url_for('index')
            })

        return jsonify({'success': False, 'message': 'Wajah tidak dikenali. Coba pencahayaan yang cukup atau gunakan password.'})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)})
    except Exception as e:
        current_app.logger.exception('Face verification failed')
        return jsonify({'success': False, 'message': 'Terjadi kesalahan saat verifikasi wajah.'}), 500


@auth_bp.route('/dongle-status', methods=['GET'])
def dongle_status():
    """Status token USB untuk tombol pemeriksaan pada dashboard."""
    return jsonify(get_dongle_status())


@auth_bp.route('/dongle-required')
def dongle_required():
    """Halaman peringatan dongle tidak terdeteksi"""
    return render_template('dongle_required.html')


@auth_bp.route('/create-dongle')
def create_dongle_page():
    """Buat file dongle untuk testing"""
    try:
        path = create_dongle_file()
        flash(f'File dongle berhasil dibuat di: {path}. Silakan login.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        flash(f'Gagal membuat dongle: {str(e)}', 'danger')
        return redirect(url_for('auth.dongle_required'))
