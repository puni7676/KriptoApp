# Mengaktifkan login wajah (MediaPipe + OpenCV LBPH)

Versi ini tidak memakai `face_recognition` atau `dlib`, sehingga tidak perlu membangun ekstensi C++ di Windows. MediaPipe digunakan untuk mendeteksi wajah dan OpenCV contrib (LBPH) untuk membandingkan potongan wajah.

## Persiapan

- Gunakan Python 3.11 64-bit dan virtual environment proyek (`.venv`).
- Jalankan PowerShell dari folder `D:\kripto-app`.
- Pastikan kamera dapat diakses browser. Pada `localhost`, browser biasanya mengizinkan kamera.

## Instalasi

Hapus paket OpenCV lama agar tidak ada dua distribusi yang memasang modul `cv2` bersamaan:

```powershell
python -m pip uninstall -y opencv-python opencv-contrib-python mediapipe
python -m pip install -r requirements-face.txt
```

Pastikan instalasi berhasil:

```powershell
python -c "import cv2, mediapipe as mp; print('OpenCV:', cv2.__version__); print('MediaPipe:', mp.__version__); print('LBPH:', hasattr(cv2, 'face'))"
```

Nilai `LBPH` harus `True`. Kemudian jalankan aplikasi:

```powershell
python app.py
```

## Cara menggunakan

1. Buka halaman registrasi dan buat akun baru.
2. Klik **Aktifkan Kamera**, posisikan wajah di tengah dengan pencahayaan cukup, lalu klik **Ambil Foto**.
3. Selesaikan registrasi. Potongan wajah yang sudah dinormalisasi disimpan pada kolom `face_encoding_data` yang sudah ada; tidak perlu mengubah skema database.
4. Pada halaman login, aktifkan kamera dan ambil foto untuk mencoba login biometrik. Login password tetap tersedia.

## Catatan akurasi dan keamanan

LBPH adalah metode pengenalan wajah klasik dan lebih sensitif terhadap perubahan cahaya, jarak, sudut, dan ekspresi dibanding model embedding modern. Ambang awal verifikasi adalah confidence `65` pada `routes/auth.py`; nilai ini mungkin perlu diuji dan disesuaikan dengan kondisi kamera. Metode ini belum memiliki liveness detection, sehingga foto/video dapat berisiko digunakan untuk spoofing. Untuk sistem produksi atau data sensitif, jangan jadikan fitur ini satu-satunya faktor autentikasi.

Data wajah dari implementasi `face_recognition` lama (jika pernah tersimpan) tidak kompatibel dengan format LBPH. Pengguna tersebut perlu mendaftarkan ulang data wajah; login dengan password tetap dapat digunakan.
