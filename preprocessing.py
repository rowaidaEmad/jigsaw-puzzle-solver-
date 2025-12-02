import cv2
import numpy as np
from typing import Optional


def denoise(image: np.ndarray, strength: int = 10) -> np.ndarray:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    denoised = cv2.fastNlMeansDenoisingColored(bgr, None, strength, strength, 7, 21)
    return cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)


def bilateral_filter(
    image: np.ndarray, d: int = 9, sigma_color: int = 75, sigma_space: int = 75
) -> np.ndarray:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    filtered = cv2.bilateralFilter(bgr, d, sigma_color, sigma_space)
    return cv2.cvtColor(filtered, cv2.COLOR_BGR2RGB)


def sharpen(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * strength
    kernel[1, 1] = 1 + 8 * strength
    kernel = kernel / kernel.sum() * 9
    sharpened = cv2.filter2D(image, -1, kernel.astype(np.float32))
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def enhance_contrast(image: np.ndarray) -> np.ndarray:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)


def gaussian_blur(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)


def preprocess(image: np.ndarray, method: str = "bilateral") -> np.ndarray:
    if method == "none":
        return image
    elif method == "denoise":
        return denoise(image)
    elif method == "bilateral":
        return bilateral_filter(image)
    elif method == "sharpen":
        return sharpen(image)
    elif method == "contrast":
        return enhance_contrast(image)
    elif method == "blur":
        return gaussian_blur(image)
    elif method == "full":
        img = denoise(image, strength=5)
        img = bilateral_filter(img, d=5, sigma_color=50, sigma_space=50)
        return img
    else:
        raise ValueError(f"Unknown preprocessing method: {method}")
