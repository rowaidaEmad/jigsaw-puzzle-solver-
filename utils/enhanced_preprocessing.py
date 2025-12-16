"""
Enhanced preprocessing pipeline based on improved results.
Includes denoising, edge enhancement, and CLAHE.
"""

import cv2
import numpy as np
from typing import Optional


def bilateral_denoise(
    image: np.ndarray, d: int = 9, sigma_color: int = 50, sigma_space: int = 50
) -> np.ndarray:
    """
    Apply bilateral filter for edge-preserving denoising.

    Args:
        image: Input image (BGR or RGB)
        d: Diameter of pixel neighborhood
        sigma_color: Filter sigma in color space
        sigma_space: Filter sigma in coordinate space

    Returns:
        Denoised image
    """
    if len(image.shape) == 2:
        # Grayscale
        return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

    # For color images, apply to each channel
    denoised = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
    return denoised


def enhance_edges(image: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE + Unsharp Mask for edge enhancement.

    This is the key enhancement from the improved project that
    significantly boosts edge detection and matching performance.

    Args:
        image: Input BGR or RGB image

    Returns:
        Enhanced image with sharper edges
    """
    # Step 1: Local contrast enhancement using CLAHE
    # Convert to LAB color space for perceptually uniform enhancement
    if len(image.shape) == 2:
        # Grayscale
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)

    # For color images, work in LAB space
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    L, A, B = cv2.split(lab)

    # Apply CLAHE to L channel only
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    L_clahe = clahe.apply(L)

    # Merge back
    lab_clahe = cv2.merge([L_clahe, A, B])
    clahe_img = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)

    # Step 2: Edge sharpening (Unsharp Mask)
    blur = cv2.GaussianBlur(clahe_img, (5, 5), 1.5)

    alpha = 1.8  # Sharpening strength
    img_sharp = cv2.addWeighted(clahe_img, 1 + alpha, blur, -alpha, 0)

    return img_sharp


def preprocess_pipeline(
    image: np.ndarray, apply_denoise: bool = True, apply_enhancement: bool = True
) -> np.ndarray:
    """
    Complete preprocessing pipeline from the improved project.

    Pipeline:
    1. Bilateral filtering (denoising)
    2. CLAHE + Unsharp mask (edge enhancement)

    Args:
        image: Input image (BGR or RGB)
        apply_denoise: Whether to apply denoising
        apply_enhancement: Whether to apply edge enhancement

    Returns:
        Preprocessed image
    """
    result = image.copy()

    if apply_denoise:
        result = bilateral_denoise(result, d=9, sigma_color=50, sigma_space=50)

    if apply_enhancement:
        result = enhance_edges(result)

    return result


def preprocess_dataset(
    input_paths: list,
    output_dir: str,
    apply_denoise: bool = True,
    apply_enhancement: bool = True,
    verbose: bool = True,
) -> int:
    """
    Preprocess a batch of images.

    Args:
        input_paths: List of input image paths
        output_dir: Directory to save processed images
        apply_denoise: Whether to apply denoising
        apply_enhancement: Whether to apply edge enhancement
        verbose: Print progress

    Returns:
        Number of images processed
    """
    import os

    os.makedirs(output_dir, exist_ok=True)
    processed = 0

    for img_path in input_paths:
        try:
            img = cv2.imread(img_path)
            if img is None:
                if verbose:
                    print(f"Failed to load: {img_path}")
                continue

            # Apply preprocessing
            processed_img = preprocess_pipeline(img, apply_denoise, apply_enhancement)

            # Save
            basename = os.path.basename(img_path)
            output_path = os.path.join(output_dir, basename)
            cv2.imwrite(output_path, processed_img)

            processed += 1

            if verbose and processed % 10 == 0:
                print(f"Processed {processed}/{len(input_paths)} images")

        except Exception as e:
            if verbose:
                print(f"Error processing {img_path}: {e}")

    if verbose:
        print(f"Completed: {processed}/{len(input_paths)} images")

    return processed
