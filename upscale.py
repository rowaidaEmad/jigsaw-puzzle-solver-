"""
Image Upscaling Module for Jigsaw Puzzle Solver

Provides the best upscaling methods for cartoon/anime puzzle images.
Selected methods: lanczos, lanczos_sharp, detail_enhance, pencil_color, guided_filter
"""

import cv2
import numpy as np


def _sharpen_image(image, strength=0.5):
    blurred = cv2.GaussianBlur(image, (0, 0), 3)
    sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
    return sharpened


def _sharpen_laplacian(image, strength=0.3):
    if len(image.shape) == 3:
        channels = cv2.split(image)
        sharpened_channels = []
        for ch in channels:
            laplacian = cv2.Laplacian(ch, cv2.CV_64F)
            sharpened = ch - strength * laplacian
            sharpened = np.clip(sharpened, 0, 255).astype(np.uint8)
            sharpened_channels.append(sharpened)
        return cv2.merge(sharpened_channels)
    else:
        laplacian = cv2.Laplacian(image, cv2.CV_64F)
        sharpened = image - strength * laplacian
        return np.clip(sharpened, 0, 255).astype(np.uint8)


# =============================================================================
# UPSCALING METHODS
# =============================================================================


def upscale_lanczos(image, scale_factor=4):
    h, w = image.shape[:2]
    return cv2.resize(
        image, (w * scale_factor, h * scale_factor), interpolation=cv2.INTER_LANCZOS4
    )


def upscale_lanczos_sharp(image, scale_factor=4):
    upscaled = upscale_lanczos(image, scale_factor)
    return _sharpen_image(upscaled, strength=0.6)


def upscale_detail_enhance(image, scale_factor=4):
    h, w = image.shape[:2]
    new_h, new_w = h * scale_factor, w * scale_factor

    # details
    enhanced = cv2.detailEnhance(image, sigma_s=10, sigma_r=0.15)

    upscaled = cv2.resize(enhanced, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # bilateral to remove noise
    upscaled = cv2.bilateralFilter(upscaled, d=5, sigmaColor=40, sigmaSpace=40)

    return _sharpen_image(upscaled, strength=0.3)


def upscale_pencil_color(image, scale_factor=4):
    h, w = image.shape[:2]
    new_h, new_w = h * scale_factor, w * scale_factor

    # pencil sketch (grayscale and color)
    _, color_sketch = cv2.pencilSketch(
        image, sigma_s=60, sigma_r=0.07, shade_factor=0.05
    )

    blended = cv2.addWeighted(image, 0.7, color_sketch, 0.3, 0)

    upscaled = cv2.resize(blended, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    return _sharpen_image(upscaled, strength=0.3)


def upscale_guided_filter(image, scale_factor=4):
    h, w = image.shape[:2]
    new_h, new_w = h * scale_factor, w * scale_factor

    # edge-aware smoothing
    radius = 8
    smooth = cv2.bilateralFilter(image, d=radius * 2 + 1, sigmaColor=50, sigmaSpace=50)

    upscaled = cv2.resize(smooth, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    sharpened = _sharpen_image(upscaled, strength=0.5)
    sharpened = _sharpen_laplacian(sharpened, strength=0.15)

    return sharpened
