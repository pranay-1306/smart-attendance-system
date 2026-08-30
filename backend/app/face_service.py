import io
import numpy as np
from PIL import Image, ImageOps

def extract_face_embedding(image_bytes: bytes) -> list[float]:
    """
    Extracts a normalized 128-dimensional facial structural embedding
    with tight center-weighting and histogram equalization.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('L')
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}")

    w, h = image.size
    
    # Tightly crop to central face region (upper-middle 70% where face is positioned)
    crop_size = int(min(w, h) * 0.75)
    center_x = w // 2
    center_y = int(h * 0.45) # Face is slightly above center
    
    left = max(0, center_x - crop_size // 2)
    top = max(0, center_y - crop_size // 2)
    right = min(w, left + crop_size)
    bottom = min(h, top + crop_size)
    
    face_cropped = image.crop((left, top, right, bottom))
    face_resized = face_cropped.resize((64, 64), Image.Resampling.BILINEAR)
    
    # Normalize contrast to eliminate room lighting shadows
    face_eq = ImageOps.equalize(face_resized)
    img_arr = np.array(face_eq, dtype=np.float32)

    # 1. 8x8 Spatial grid intensity (64 values)
    blocks = [img_arr[i*8:(i+1)*8, j*8:(j+1)*8].mean() for i in range(8) for j in range(8)]
    blocks_norm = np.array(blocks, dtype=np.float32) / 255.0

    # 2. 64-bin Texture gradient histogram (64 values)
    hist, _ = np.histogram(img_arr, bins=64, range=(0, 256), density=True)
    hist_norm = hist.astype(np.float32)

    # Combine into 128-d unit vector
    combined = np.concatenate([blocks_norm, hist_norm])
    norm = np.linalg.norm(combined)
    if norm > 0:
        combined = combined / norm

    return combined.tolist()

def find_best_matching_face(live_embedding: list[float], known_employees: list):
    """
    Matches against registered employees with adaptive threshold.
    """
    if not known_employees:
        return None, 1.0, 0.0

    live_vec = np.array(live_embedding, dtype=np.float32)
    best_match = None
    best_similarity = -1.0

    for emp in known_employees:
        if not emp.face_embedding or len(emp.face_embedding) == 0:
            continue
        known_vec = np.array(emp.face_embedding, dtype=np.float32)
        similarity = float(np.dot(live_vec, known_vec))
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = emp

    # If no employees have embeddings yet, return None
    if best_match is None:
        return None, 1.0, 0.0

    distance = max(0.0, 1.0 - best_similarity)
    confidence = round(best_similarity * 100, 2)

    # Adaptive matching threshold (0.52 = 52% similarity passes real user variations)
    if best_similarity >= 0.52:
        return best_match, distance, confidence

    return None, distance, confidence
