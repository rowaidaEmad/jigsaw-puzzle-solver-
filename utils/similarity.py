"""
Similarity Functions for Jigsaw Puzzle Solving

Each function takes two pieces and an orientation, returns a dissimilarity score.
Lower score = better match.

Orientation: 0=top, 1=bottom, 2=left, 3=right
(where p2 is placed relative to p1)
"""

import cv2
import numpy as np
from typing import Optional


# ============================================================================
# CONFIGURATION - Modify these values to tune similarity metrics
# ============================================================================

# Color comparison depth (how many pixel rows/cols to compare at edges)
# Higher = considers more pixels from the edge, slower but more accurate
COLOR_DEPTH = 2

# Edge comparison depth (how many pixel rows/cols to sample from binary edges)
# Higher = compares more of the edge strip, can help with noisy edges
EDGE_DEPTH = 1

# Histogram comparison parameters
HISTOGRAM_BINS = 32              # Number of bins for color histogram
HISTOGRAM_EDGE_DEPTH = 3         # Pixel depth for histogram region

# Texture comparison depth
# Higher = considers larger region for texture analysis
TEXTURE_DEPTH = 5

# Use LAB color space instead of RGB for color comparisons
# LAB is perceptually uniform, often better for color matching
USE_LAB_COLOR = True

# ============================================================================


def rgb_to_lab(image: np.ndarray) -> np.ndarray:
    """Convert RGB image to LAB color space."""
    if len(image.shape) == 2:
        return image.astype(np.float32)
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)


def to_gray(image: np.ndarray) -> np.ndarray:
    """Convert to grayscale if needed."""
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return image


# --- Similarity Functions ---


def color_ssd(
    p1: np.ndarray,
    p2: np.ndarray,
    orientation: int,
    use_lab: bool = True,
    depth: int = 1,
) -> float:
    """
    Sum of squared differences between adjacent edges.

    Args:
        depth: How many rows/cols to compare (1 = edge only)
    """
    if use_lab:
        p1, p2 = rgb_to_lab(p1), rgb_to_lab(p2)
    else:
        p1, p2 = p1.astype(np.float32), p2.astype(np.float32)

    total = 0.0
    for d in range(depth):
        w = 1.0 / (d + 1)
        if orientation == 0:  # p2 above p1
            e1, e2 = p1[d, :], p2[-(d + 1), :]
        elif orientation == 1:  # p2 below p1
            e1, e2 = p1[-(d + 1), :], p2[d, :]
        elif orientation == 2:  # p2 left of p1
            e1, e2 = p1[:, d], p2[:, -(d + 1)]
        else:  # p2 right of p1
            e1, e2 = p1[:, -(d + 1)], p2[:, d]
        total += w * float(np.sum((e1 - e2) ** 2))
    return total


def gradient_compatibility(p1: np.ndarray, p2: np.ndarray, orientation: int) -> float:
    """
    Mahalanobis Gradient Compatibility.
    Predicts continuation of gradients across the boundary.
    """
    p1, p2 = rgb_to_lab(p1), rgb_to_lab(p2)

    if orientation == 0:
        p1_inner, p1_edge = p1[1, :], p1[0, :]
        p2_edge, p2_inner = p2[-1, :], p2[-2, :]
    elif orientation == 1:
        p1_inner, p1_edge = p1[-2, :], p1[-1, :]
        p2_edge, p2_inner = p2[0, :], p2[1, :]
    elif orientation == 2:
        p1_inner, p1_edge = p1[:, 1], p1[:, 0]
        p2_edge, p2_inner = p2[:, -1], p2[:, -2]
    else:
        p1_inner, p1_edge = p1[:, -2], p1[:, -1]
        p2_edge, p2_inner = p2[:, 0], p2[:, 1]

    grad1 = p1_edge - p1_inner
    grad2 = p2_inner - p2_edge
    pred_p2 = p1_edge + grad1
    pred_p1 = p2_edge + grad2

    err1 = pred_p2 - p2_edge
    err2 = pred_p1 - p1_edge
    return float(np.sum(err1**2) + np.sum(err2**2))


def histogram_similarity(
    p1: np.ndarray,
    p2: np.ndarray,
    orientation: int,
    bins: int = 32,
    edge_depth: int = 3,
) -> float:
    """Compare color histograms of edge regions."""
    if orientation == 0:
        r1, r2 = p1[:edge_depth, :], p2[-edge_depth:, :]
    elif orientation == 1:
        r1, r2 = p1[-edge_depth:, :], p2[:edge_depth, :]
    elif orientation == 2:
        r1, r2 = p1[:, :edge_depth], p2[:, -edge_depth:]
    else:
        r1, r2 = p1[:, -edge_depth:], p2[:, :edge_depth]

    total = 0.0
    for c in range(3):
        h1, _ = np.histogram(r1[:, :, c].flatten(), bins=bins, range=(0, 256))
        h2, _ = np.histogram(r2[:, :, c].flatten(), bins=bins, range=(0, 256))
        h1 = h1.astype(np.float32).reshape(-1)
        h2 = h2.astype(np.float32).reshape(-1)
        h1 /= h1.sum() + 1e-10
        h2 /= h2.sum() + 1e-10
        total += float(cv2.compareHist(h1, h2, cv2.HISTCMP_CHISQR))
    return total


def edge_gradient(p1: np.ndarray, p2: np.ndarray, orientation: int) -> float:
    """Compare edge gradients using Sobel operator."""
    g1, g2 = to_gray(p1), to_gray(p2)

    if orientation in [0, 1]:
        s1 = cv2.Sobel(g1, cv2.CV_64F, 0, 1, ksize=3)
        s2 = cv2.Sobel(g2, cv2.CV_64F, 0, 1, ksize=3)
        e1 = s1[0, :] if orientation == 0 else s1[-1, :]
        e2 = s2[-1, :] if orientation == 0 else s2[0, :]
    else:
        s1 = cv2.Sobel(g1, cv2.CV_64F, 1, 0, ksize=3)
        s2 = cv2.Sobel(g2, cv2.CV_64F, 1, 0, ksize=3)
        e1 = s1[:, 0] if orientation == 2 else s1[:, -1]
        e2 = s2[:, -1] if orientation == 2 else s2[:, 0]

    return float(np.sum((e1 - e2) ** 2))


def contour_match(
    c1: Optional[np.ndarray],
    c2: Optional[np.ndarray],
    orientation: int,
) -> float:
    """Compare contour images at edges."""
    if c1 is None or c2 is None:
        return 0.0

    if orientation == 0:
        e1, e2 = c1[0, :], c2[-1, :]
    elif orientation == 1:
        e1, e2 = c1[-1, :], c2[0, :]
    elif orientation == 2:
        e1, e2 = c1[:, 0], c2[:, -1]
    else:
        e1, e2 = c1[:, -1], c2[:, 0]

    return float(np.sum((e1.astype(np.float32) - e2.astype(np.float32)) ** 2))


def texture_match(
    p1: np.ndarray, p2: np.ndarray, orientation: int, depth: int = 5
) -> float:
    """Compare texture using Laplacian variance."""
    g1, g2 = to_gray(p1), to_gray(p2)

    if orientation == 0:
        r1, r2 = g1[:depth, :], g2[-depth:, :]
    elif orientation == 1:
        r1, r2 = g1[-depth:, :], g2[:depth, :]
    elif orientation == 2:
        r1, r2 = g1[:, :depth], g2[:, -depth:]
    else:
        r1, r2 = g1[:, -depth:], g2[:, :depth]

    var1 = np.var(cv2.Laplacian(r1, cv2.CV_64F))
    var2 = np.var(cv2.Laplacian(r2, cv2.CV_64F))
    return float(abs(var1 - var2))


def _is_binary_edge_image(img: np.ndarray) -> bool:
    """Check if image is a binary edge image (black background, white edges)."""
    gray = to_gray(img)
    unique = np.unique(gray)
    return len(unique) == 2 and 0 in unique and 255 in unique


def edge_gradient_binary(
    p1: np.ndarray, p2: np.ndarray, orientation: int, depth: int = 1
) -> float:
    """
    Compare preprocessed binary edge images directly.
    Samples a strip of 'depth' pixels at the boundary and compares edge presence.

    Args:
        p1, p2: Binary edge images (0=no edge, 255=edge)
        orientation: 0=top, 1=bottom, 2=left, 3=right
        depth: How many pixel rows/cols to sample from the border

    Returns:
        Fraction of mismatched edge pixels [0, 1]
    """
    g1, g2 = to_gray(p1), to_gray(p2)

    # Extract edge strips based on orientation
    if orientation == 0:  # p2 above p1
        strip1 = g1[:depth, :]
        strip2 = g2[-depth:, :]
    elif orientation == 1:  # p2 below p1
        strip1 = g1[-depth:, :]
        strip2 = g2[:depth, :]
    elif orientation == 2:  # p2 left of p1
        strip1 = g1[:, :depth]
        strip2 = g2[:, -depth:]
    else:  # p2 right of p1
        strip1 = g1[:, -depth:]
        strip2 = g2[:, :depth]

    # Binarize (in case of any compression artifacts)
    strip1 = (strip1 > 127).astype(np.uint8)
    strip2 = (strip2 > 127).astype(np.uint8)

    # Calculate fraction of mismatched edge pixels
    diff = np.abs(strip1.astype(np.int16) - strip2.astype(np.int16))
    mismatch_fraction = np.sum(diff) / diff.size

    return float(mismatch_fraction)


# --- Combined Calculator ---


class SimilarityCalculator:
    """
    Weighted combination of similarity functions using preprocessed piece types.

    Each metric uses the appropriate preprocessed version:
        - color: Uses upscaled pieces
        - gradient: Uses upscaled pieces
        - histogram: Uses upscaled pieces
        - edge: Uses edge-extracted pieces
        - contour: Uses contour pieces
        - texture: Uses preprocessed pieces
    """

    def __init__(
        self,
        weight_color: float = 1.0,
        weight_gradient: float = 0.5,
        weight_histogram: float = 0.2,
        weight_edge: float = 0.3,
        weight_contour: float = 0.2,
        weight_texture: float = 0.1,
    ):
        self.w_color = weight_color
        self.w_gradient = weight_gradient
        self.w_histogram = weight_histogram
        self.w_edge = weight_edge
        self.w_contour = weight_contour
        self.w_texture = weight_texture

    def compute(
        self,
        idx1: int,
        idx2: int,
        orientation: int,
        pieces_dict: dict,
    ) -> float:
        """
        Compute combined dissimilarity using preprocessed pieces.

        Args:
            idx1, idx2: Piece indices
            orientation: 0=top, 1=bottom, 2=left, 3=right
            pieces_dict: Dict with keys 'original', 'upscaled', 'edges', 'contours', 'prep', 'binary'

        Returns:
            Dissimilarity score (lower = better match)
        """
        total = 0.0

        # Color comparison: use upscaled pieces
        if self.w_color > 0 and "upscaled" in pieces_dict:
            p1, p2 = pieces_dict["upscaled"][idx1], pieces_dict["upscaled"][idx2]
            total += self.w_color * color_ssd(
                p1, p2, orientation, USE_LAB_COLOR, COLOR_DEPTH
            )

        # Gradient compatibility: use upscaled pieces
        if self.w_gradient > 0 and "upscaled" in pieces_dict:
            p1, p2 = pieces_dict["upscaled"][idx1], pieces_dict["upscaled"][idx2]
            total += self.w_gradient * gradient_compatibility(p1, p2, orientation)

        # Histogram: use upscaled pieces
        if self.w_histogram > 0 and "upscaled" in pieces_dict:
            p1, p2 = pieces_dict["upscaled"][idx1], pieces_dict["upscaled"][idx2]
            total += self.w_histogram * histogram_similarity(
                p1, p2, orientation, HISTOGRAM_BINS, HISTOGRAM_EDGE_DEPTH
            )

        # Edge gradient: use preprocessed edge images
        if self.w_edge > 0 and "edges" in pieces_dict:
            e1, e2 = pieces_dict["edges"][idx1], pieces_dict["edges"][idx2]
            # Use binary edge comparison with configured depth
            total += self.w_edge * edge_gradient_binary(
                e1, e2, orientation, EDGE_DEPTH
            )

        # Contour matching: use contour images
        if self.w_contour > 0 and "contours" in pieces_dict:
            c1, c2 = pieces_dict["contours"][idx1], pieces_dict["contours"][idx2]
            total += self.w_contour * contour_match(c1, c2, orientation)

        # Texture: use prep pieces
        if self.w_texture > 0 and "prep" in pieces_dict:
            p1, p2 = pieces_dict["prep"][idx1], pieces_dict["prep"][idx2]
            total += self.w_texture * texture_match(p1, p2, orientation, TEXTURE_DEPTH)

        return total
