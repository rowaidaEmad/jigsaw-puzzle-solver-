import cv2
import numpy as np
from typing import List, Tuple


def load_image(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def save_image(image: np.ndarray, path: str) -> None:
    img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(path, img_bgr)


def split_image(image: np.ndarray, piece_size: int) -> List[np.ndarray]:
    height, width = image.shape[:2]
    grid_rows = height // piece_size
    grid_cols = width // piece_size

    pieces = []
    for row in range(grid_rows):
        for col in range(grid_cols):
            y_start = row * piece_size
            y_end = y_start + piece_size
            x_start = col * piece_size
            x_end = x_start + piece_size
            piece = image[y_start:y_end, x_start:x_end].copy()
            pieces.append(piece)
    return pieces


def merge_pieces(
    pieces: List[np.ndarray], arrangement: List[int], grid_size: int
) -> np.ndarray:
    piece_size = pieces[0].shape[0]
    channels = pieces[0].shape[2] if len(pieces[0].shape) == 3 else 1
    image_size = grid_size * piece_size

    if channels > 1:
        result = np.zeros((image_size, image_size, channels), dtype=np.uint8)
    else:
        result = np.zeros((image_size, image_size), dtype=np.uint8)

    for idx, piece_idx in enumerate(arrangement):
        row = idx // grid_size
        col = idx % grid_size
        y_start = row * piece_size
        y_end = y_start + piece_size
        x_start = col * piece_size
        x_end = x_start + piece_size
        result[y_start:y_end, x_start:x_end] = pieces[piece_idx]
    return result


def get_image_dimensions(image: np.ndarray) -> Tuple[int, int, int]:
    if len(image.shape) == 2:
        return image.shape[0], image.shape[1], 1
    return image.shape[0], image.shape[1], image.shape[2]
