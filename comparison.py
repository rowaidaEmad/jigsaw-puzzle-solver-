import cv2
import numpy as np
from typing import Tuple


def compare_images(img1: np.ndarray, img2: np.ndarray, tolerance: float = 50.0) -> bool:
    if img1.shape[:2] != img2.shape[:2]:
        return False
    if len(img1.shape) == 3 and img1.shape[2] == 4:
        img1 = img1[:, :, :3]
    if len(img2.shape) == 3 and img2.shape[2] == 4:
        img2 = img2[:, :, :3]
    diff = np.abs(img1.astype(float) - img2.astype(float))
    avg_diff = np.mean(diff)
    return avg_diff < tolerance


def compare_piece_positions(
    output_img: np.ndarray, correct_img: np.ndarray, piece_size: int
) -> bool:
    h, w = output_img.shape[:2]
    grid_size = h // piece_size
    matches = 0
    total = grid_size * grid_size
    for i in range(grid_size):
        for j in range(grid_size):
            y1, y2 = i * piece_size, (i + 1) * piece_size
            x1, x2 = j * piece_size, (j + 1) * piece_size
            piece_out = output_img[y1:y2, x1:x2]
            piece_cor = correct_img[y1:y2, x1:x2]
            if compare_images(piece_out, piece_cor):
                matches += 1
    return (matches / total) >= 0.8


def evaluate_accuracy(
    output_dir: str, correct_dir: str, prefix: str, num_images: int, piece_size: int
) -> Tuple[int, int, float, list]:
    correct_count = 0
    total_count = 0
    failed_images = []
    for i in range(num_images):
        output_path = f"{output_dir}/{prefix}{i}_ans.png"
        correct_path = f"{correct_dir}/{i}.png"
        try:
            output_img = cv2.imread(output_path)
            correct_img = cv2.imread(correct_path)
            if output_img is None or correct_img is None:
                continue
            output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
            correct_img = cv2.cvtColor(correct_img, cv2.COLOR_BGR2RGB)
            total_count += 1
            match_simple = compare_images(output_img, correct_img)
            match_positions = compare_piece_positions(
                output_img, correct_img, piece_size
            )
            if match_simple or match_positions:
                correct_count += 1
            else:
                failed_images.append(i)
        except Exception as e:
            print(f"Error processing image {i}: {e}")
            continue
    accuracy = (100.0 * correct_count / total_count) if total_count > 0 else 0.0
    return correct_count, total_count, accuracy, failed_images
