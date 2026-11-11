"""Face detection and lightweight face matching using MediaPipe + OpenCV LBPH.

This avoids dlib/face_recognition. LBPH is a traditional, lighting-sensitive
recognizer and should be treated as a convenience login factor, not high-security
biometric authentication.
"""
import base64
import json

import cv2
import mediapipe as mp
import numpy as np

_FACE_DETECTION = mp.solutions.face_detection.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.5,
)


def _decode_data_url(data_url: str) -> np.ndarray:
    if not isinstance(data_url, str) or "," not in data_url:
        raise ValueError("Format gambar tidak valid.")
    encoded = data_url.split(",", 1)[1]
    raw = base64.b64decode(encoded, validate=True)
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Gambar tidak dapat dibaca.")
    return image


def extract_face(data_url: str) -> np.ndarray:
    """Detect the largest face and return a normalized 100x100 grayscale crop."""
    image = _decode_data_url(data_url)
    height, width = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = _FACE_DETECTION.process(rgb)
    if not result.detections:
        raise ValueError("Wajah tidak terdeteksi. Posisikan wajah di depan kamera.")

    detection = max(
        result.detections,
        key=lambda item: item.location_data.relative_bounding_box.width
        * item.location_data.relative_bounding_box.height,
    )
    box = detection.location_data.relative_bounding_box
    x1 = max(0, int(box.xmin * width))
    y1 = max(0, int(box.ymin * height))
    x2 = min(width, int((box.xmin + box.width) * width))
    y2 = min(height, int((box.ymin + box.height) * height))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("Area wajah tidak valid. Coba ambil foto ulang.")

    face = image[y1:y2, x1:x2]
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    return cv2.resize(gray, (100, 100), interpolation=cv2.INTER_AREA)


def encode_face(data_url: str) -> str:
    face = extract_face(data_url)
    return json.dumps(face.astype(np.uint8).tolist(), separators=(",", ":"))


def compare_faces(stored_json: str, captured_face: np.ndarray):
    """Return LBPH confidence (lower is closer); caller applies threshold."""
    stored = np.asarray(json.loads(stored_json), dtype=np.uint8)
    if stored.shape != (100, 100):
        raise ValueError("Data biometrik tersimpan memiliki format yang tidak valid.")
    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0
    )
    recognizer.train([stored], np.asarray([1], dtype=np.int32))
    _label, confidence = recognizer.predict(captured_face)
    return float(confidence)
