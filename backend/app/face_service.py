import io
import numpy as np
from PIL import Image, ImageOps

def extract_face_embedding(image_bytes: bytes) -> list[float]:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('L')
    except Exception as e:
        raise ValueError(f'Invalid image data: {str(e)}')

    w, h = image.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    cropped = image.crop((left, top, left + min_dim, top + min_dim))
    resized = cropped.resize((64, 64), Image.Resampling.BILINEAR)

    equalized = ImageOps.equalize(resized)
    img_arr = np.array(equalized, dtype=np.float32)

    blocks = [img_arr[i*8:(i+1)*8, j*8:(j+1)*8].mean() for i in range(8) for j in range(8)]
    hist, _ = np.histogram(img_arr, bins=64, range=(0, 256), density=True)

    blocks_norm = np.array(blocks, dtype=np.float32) / 255.0
    hist_norm = hist.astype(np.float32)

    combined = np.concatenate([blocks_norm, hist_norm])
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm

    return combined.tolist()

def find_best_matching_face(live_embedding: list[float], known_employees: list):
    if not known_employees:
        return None, 1.0, 0.0

    live_vec = np.array(live_embedding, dtype=np.float32)
    best_match = None
    best_similarity = -1.0

    for emp in known_employees:
        known_vec = np.array(emp.face_embedding, dtype=np.float32)
        similarity = float(np.dot(live_vec, known_vec))
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = emp

    distance = max(0.0, 1.0 - best_similarity)
    confidence = round(best_similarity * 100, 2)

    if best_similarity >= 0.70 and best_match is not None:
        return best_match, distance, confidence

    return None, distance, confidence
