"""
Script inisialisasi database dan pembuatan user admin untuk testing.
Jalankan sekali sebelum pertama kali menjalankan aplikasi:
  python init_db.py
"""

from app import create_app
from models import db, User
from crypto_utils import hash_password, create_dongle_file

def init_database():
    app = create_app()
    with app.app_context():
        # Buat semua tabel
        db.create_all()
        print("[OK] Database tables created.")

        # Buat user admin jika belum ada
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=hash_password('admin123'),
                face_encoding_data=None
            )
            db.session.add(admin)
            db.session.commit()
            print("[OK] User 'admin' created (password: admin123)")
        else:
            print("[INFO] User 'admin' already exists.")

        # Buat user demo kedua untuk testing kirim pesan
        if not User.query.filter_by(username='demo').first():
            demo = User(
                username='demo',
                password_hash=hash_password('demo123'),
                face_encoding_data=None
            )
            db.session.add(demo)
            db.session.commit()
            print("[OK] User 'demo' created (password: demo123)")
        else:
            print("[INFO] User 'demo' already exists.")

    # Buat file dongle lokal untuk testing
    dongle_path = create_dongle_file()
    print(f"[OK] Dongle file created at: {dongle_path}")

    print("\n=== Inisialisasi selesai! ===")
    print("Jalankan aplikasi dengan: python app.py")
    print("Buka browser: http://localhost:5000")
    print("\nAkun testing:")
    print("  Username: admin | Password: admin123")
    print("  Username: demo  | Password: demo123")

if __name__ == '__main__':
    init_database()
