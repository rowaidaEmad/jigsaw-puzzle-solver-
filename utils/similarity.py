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
# For small pieces: 2-3 pixels is optimal
COLOR_DEPTH = 1

# Edge comparison depth (how many pixel rows/cols to sample from binary edges)
# Higher = compares more of the edge strip, can help with noisy edges
# For small pieces: use 2-3 pixels (too high reduces discriminative power)
EDGE_DEPTH = 1

# Black border filtering threshold
# Pixels with RGB values below this threshold (in all channels) will be ignored
# in color similarity calculations. Set to 0 to disable filtering.
# Typical values: 10-30 for strict filtering, 50-80 for moderate filtering
BLACK_THRESHOLD = 20

# Histogram comparison parameters
HISTOGRAM_BINS = 32  # Number of bins for color histogram
HISTOGRAM_EDGE_DEPTH = 3  # Pixel depth for histogram region

# Texture comparison depth
# Higher = considers larger region for texture analysis
TEXTURE_DEPTH = 5

# Use LAB color space instead of RGB for color comparisons
# LAB is perceptually uniform, often better for color matching
USE_LAB_COLOR = True

# Proximity matching configuration
# When comparing binary edge/contour strips we also consider nearby pixels
# within PROXIMITY_TOLERANCE. If a pixel in one strip has a nearby pixel
# in the neighbour strip we consider that a 'match' (+1); otherwise it's a
# 'miss' (-1). The proximity weights control how much this helps/hurts
# the resulting dissimilarity (positive lowers dissimilarity when matches
# dominate, negative increases when misses dominate).
# For combined matching with small pieces, use moderate tolerance (2-3)
PROXIMITY_TOLERANCE = 2
PROXIMITY_WEIGHT_EDGE = 0.5
PROXIMITY_WEIGHT_CONTOUR = 0.5

# ============================================================================
# WEIGHTS - configure these to tune the combined similarity scoring
# Optimized edge-only matching with enhanced features
# ============================================================================
WEIGHT_COLOR = 5.0
WEIGHT_GRADIENT = 1
WEIGHT_HISTOGRAM = 0.2
WEIGHT_EDGE = 0.8
WEIGHT_CONTOUR = 1
WEIGHT_TEXTURE = 0.2

# ============================================================================
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
    black_threshold: int = BLACK_THRESHOLD,
) -> float:
    """
    Sum of squared differences between adjacent edges.
    Black/dark pixels (below black_threshold) are ignored in the comparison.

    Args:
        depth: How many rows/cols to compare (1 = edge only)
        black_threshold: Pixels with all RGB channels below this value are ignored
    """
    # Store original RGB values for black detection
    p1_rgb = p1.copy()
    p2_rgb = p2.copy()

    if use_lab:
        p1, p2 = rgb_to_lab(p1), rgb_to_lab(p2)
    else:
        p1, p2 = p1.astype(np.float32), p2.astype(np.float32)

    total = 0.0
    valid_pixels_total = 0

    for d in range(depth):
        w = 1.0 / (d + 1)
        if orientation == 0:  # p2 above p1
            e1, e2 = p1[d, :], p2[-(d + 1), :]
            e1_rgb, e2_rgb = p1_rgb[d, :], p2_rgb[-(d + 1), :]
        elif orientation == 1:  # p2 below p1
            e1, e2 = p1[-(d + 1), :], p2[d, :]
            e1_rgb, e2_rgb = p1_rgb[-(d + 1), :], p2_rgb[d, :]
        elif orientation == 2:  # p2 left of p1
            e1, e2 = p1[:, d], p2[:, -(d + 1)]
            e1_rgb, e2_rgb = p1_rgb[:, d], p2_rgb[:, -(d + 1)]
        else:  # p2 right of p1
            e1, e2 = p1[:, -(d + 1)], p2[:, d]
            e1_rgb, e2_rgb = p1_rgb[:, -(d + 1)], p2_rgb[:, d]

        # Create mask for non-black pixels
        # A pixel is considered black if ALL channels are below the threshold
        if len(e1_rgb.shape) == 2 and e1_rgb.shape[-1] == 3:
            mask1 = np.any(e1_rgb >= black_threshold, axis=-1)
            mask2 = np.any(e2_rgb >= black_threshold, axis=-1)
        else:
            # Grayscale or single channel
            mask1 = e1_rgb >= black_threshold
            mask2 = e2_rgb >= black_threshold

        # Only consider pixels where BOTH are non-black
        valid_mask = mask1 & mask2

        if np.any(valid_mask):
            # Compute SSD only for valid (non-black) pixels
            if len(e1.shape) == 2:  # Multi-channel (LAB or RGB)
                diff_sq = np.sum((e1[valid_mask] - e2[valid_mask]) ** 2, axis=-1)
            else:  # Single channel
                diff_sq = (e1[valid_mask] - e2[valid_mask]) ** 2

            total += w * float(np.sum(diff_sq))
            valid_pixels_total += np.sum(valid_mask)

    # If all pixels were black, return a high penalty to discourage this match
    if valid_pixels_total == 0:
        return 1e6

    return total


def gradient_compatibility(
    p1: np.ndarray,
    p2: np.ndarray,
    orientation: int,
    black_threshold: int = BLACK_THRESHOLD,
) -> float:
    """
    Mahalanobis Gradient Compatibility.
    Predicts continuation of gradients across the boundary.
    Black/dark pixels are ignored in the comparison.
    """
    # Store original RGB for black detection
    p1_rgb = p1.copy()
    p2_rgb = p2.copy()

    p1, p2 = rgb_to_lab(p1), rgb_to_lab(p2)

    if orientation == 0:
        p1_inner, p1_edge = p1[1, :], p1[0, :]
        p2_edge, p2_inner = p2[-1, :], p2[-2, :]
        p1_inner_rgb, p1_edge_rgb = p1_rgb[1, :], p1_rgb[0, :]
        p2_edge_rgb, p2_inner_rgb = p2_rgb[-1, :], p2_rgb[-2, :]
    elif orientation == 1:
        p1_inner, p1_edge = p1[-2, :], p1[-1, :]
        p2_edge, p2_inner = p2[0, :], p2[1, :]
        p1_inner_rgb, p1_edge_rgb = p1_rgb[-2, :], p1_rgb[-1, :]
        p2_edge_rgb, p2_inner_rgb = p2_rgb[0, :], p2_rgb[1, :]
    elif orientation == 2:
        p1_inner, p1_edge = p1[:, 1], p1[:, 0]
        p2_edge, p2_inner = p2[:, -1], p2[:, -2]
        p1_inner_rgb, p1_edge_rgb = p1_rgb[:, 1], p1_rgb[:, 0]
        p2_edge_rgb, p2_inner_rgb = p2_rgb[:, -1], p2_rgb[:, -2]
    else:
        p1_inner, p1_edge = p1[:, -2], p1[:, -1]
        p2_edge, p2_inner = p2[:, 0], p2[:, 1]
        p1_inner_rgb, p1_edge_rgb = p1_rgb[:, -2], p1_rgb[:, -1]
        p2_edge_rgb, p2_inner_rgb = p2_rgb[:, 0], p2_rgb[:, 1]

    # Create masks for non-black pixels
    if len(p1_edge_rgb.shape) == 2:
        mask1 = np.any(p1_edge_rgb >= black_threshold, axis=-1)
        mask2 = np.any(p2_edge_rgb >= black_threshold, axis=-1)
    else:
        mask1 = p1_edge_rgb >= black_threshold
        mask2 = p2_edge_rgb >= black_threshold

    valid_mask = mask1 & mask2

    if not np.any(valid_mask):
        return 1e6

    grad1 = p1_edge - p1_inner
    grad2 = p2_inner - p2_edge
    pred_p2 = p1_edge + grad1
    pred_p1 = p2_edge + grad2

    err1 = pred_p2 - p2_edge
    err2 = pred_p1 - p1_edge

    # Only compute error for valid (non-black) pixels
    if len(err1.shape) == 2:
        err1_filtered = err1[valid_mask]
        err2_filtered = err2[valid_mask]
    else:
        err1_filtered = err1[valid_mask]
        err2_filtered = err2[valid_mask]

    return float(np.sum(err1_filtered**2) + np.sum(err2_filtered**2))


def histogram_similarity(
    p1: np.ndarray,
    p2: np.ndarray,
    orientation: int,
    bins: int = 32,
    edge_depth: int = 3,
    black_threshold: int = BLACK_THRESHOLD,
) -> float:
    """
    Compare color histograms of edge regions.
    Black/dark pixels are excluded from the histogram.
    """
    if orientation == 0:
        r1, r2 = p1[:edge_depth, :], p2[-edge_depth:, :]
    elif orientation == 1:
        r1, r2 = p1[-edge_depth:, :], p2[:edge_depth, :]
    elif orientation == 2:
        r1, r2 = p1[:, :edge_depth], p2[:, -edge_depth:]
    else:
        r1, r2 = p1[:, -edge_depth:], p2[:, :edge_depth]

    # Create mask for non-black pixels
    if len(r1.shape) == 3:
        mask1 = np.any(r1 >= black_threshold, axis=-1)
        mask2 = np.any(r2 >= black_threshold, axis=-1)
    else:
        mask1 = r1 >= black_threshold
        mask2 = r2 >= black_threshold

    if not np.any(mask1) or not np.any(mask2):
        return 1e6

    total = 0.0
    for c in range(3):
        # Only include non-black pixels in histogram
        r1_filtered = r1[:, :, c][mask1]
        r2_filtered = r2[:, :, c][mask2]

        if len(r1_filtered) == 0 or len(r2_filtered) == 0:
            continue

        h1, _ = np.histogram(r1_filtered.flatten(), bins=bins, range=(0, 256))
        h2, _ = np.histogram(r2_filtered.flatten(), bins=bins, range=(0, 256))
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
    # Extract edge vectors
    if orientation == 0:
        e1, e2 = c1[0, :], c2[-1, :]
    elif orientation == 1:
        e1, e2 = c1[-1, :], c2[0, :]
    elif orientation == 2:
        e1, e2 = c1[:, 0], c2[:, -1]
    else:
        e1, e2 = c1[:, -1], c2[:, 0]

    # Binarize contours (0/1)
    b1 = (e1 > 127).astype(np.uint8)
    b2 = (e2 > 127).astype(np.uint8)

    N = b1.size
    if N == 0:
        return 0.0

    # Baseline mismatch fraction
    baseline_mismatch = (
        float(np.sum(np.abs(b1.astype(np.int32) - b2.astype(np.int32)))) / N
    )

    # Proximity matching (symmetric): count positions in b1 that have a nearby 1 in b2
    tol = PROXIMITY_TOLERANCE
    matches = 0
    # b1 -> b2
    for i in range(N):
        if b1.flat[i] == 1:
            start = max(0, i - tol)
            end = min(N, i + tol + 1)
            if np.any(b2.flat[start:end] == 1):
                matches += 1
    # b2 -> b1
    for i in range(N):
        if b2.flat[i] == 1:
            start = max(0, i - tol)
            end = min(N, i + tol + 1)
            if np.any(b1.flat[start:end] == 1):
                matches += 1

    total_positions = 2 * N
    misses = total_positions - matches
    proximity_score = (matches - misses) / max(1, total_positions)

    final = baseline_mismatch - (PROXIMITY_WEIGHT_CONTOUR * proximity_score)
    final = max(0.0, min(1.0, final))
    return float(final)


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
    p1: np.ndarray,
    p2: np.ndarray,
    orientation: int,
    depth: int = 1,
    tolerance: int = PROXIMITY_TOLERANCE,
) -> float:
    """
    Compare preprocessed binary edge images directly with tolerance for misalignment.
    Samples a strip of 'depth' pixels at the boundary and compares edge presence,
    considering a tolerance window around each pixel in the neighboring image.

    Args:
        p1, p2: Binary edge images (0=no edge, 255=edge)
        orientation: 0=top, 1=bottom, 2=left, 3=right
        depth: How many pixel rows/cols to sample from the border
        tolerance: Number of extra pixels to check around each neighbor pixel (default: 2)

    Returns:
        Fraction of mismatched edge pixels [0, 1]
    """
    g1, g2 = to_gray(p1), to_gray(p2)

    # Extract edge strips based on orientation
    # For strip2, we extract a wider region to allow for tolerance
    if orientation == 0:  # p2 above p1
        strip1 = g1[:depth, :]
        # Extract more rows from p2 to allow tolerance window
        start_idx = max(0, g2.shape[0] - depth - tolerance)
        strip2_wide = g2[start_idx:, :]
    elif orientation == 1:  # p2 below p1
        strip1 = g1[-depth:, :]
        # Extract more rows from p2 to allow tolerance window
        end_idx = min(g2.shape[0], depth + tolerance)
        strip2_wide = g2[:end_idx, :]
    elif orientation == 2:  # p2 left of p1
        strip1 = g1[:, :depth]
        # Extract more columns from p2 to allow tolerance window
        start_idx = max(0, g2.shape[1] - depth - tolerance)
        strip2_wide = g2[:, start_idx:]
    else:  # p2 right of p1
        strip1 = g1[:, -depth:]
        # Extract more columns from p2 to allow tolerance window
        end_idx = min(g2.shape[1], depth + tolerance)
        strip2_wide = g2[:, :end_idx]

    # Binarize (in case of any compression artifacts)
    strip1 = (strip1 > 127).astype(np.uint8)
    strip2_wide = (strip2_wide > 127).astype(np.uint8)

    # For each pixel in strip1, find the best match within the tolerance window in strip2
    if orientation in [0, 1]:  # Vertical orientation
        total_mismatch = 0
        total_positions = depth * strip1.shape[1]
        for row_offset in range(depth):
            for col in range(strip1.shape[1]):
                pixel1 = int(strip1[row_offset, col])

                # Determine the search window in strip2_wide
                if orientation == 0:
                    # For top orientation, match from bottom of strip2_wide
                    center_row = strip2_wide.shape[0] - depth + row_offset
                else:
                    # For bottom orientation, match from top of strip2_wide
                    center_row = row_offset

                # Search in a tolerance window around the expected position
                found_match = False
                for dr in range(-tolerance, tolerance + 1):
                    search_row = center_row + dr
                    if 0 <= search_row < strip2_wide.shape[0]:
                        pixel2 = int(strip2_wide[search_row, col])
                        if pixel1 == pixel2:
                            found_match = True
                            break

                if not found_match:
                    total_mismatch += 1

        mismatch_fraction = total_mismatch / max(1, total_positions)
    else:  # Horizontal orientation
        total_mismatch = 0
        total_positions = depth * strip1.shape[0]
        for col_offset in range(depth):
            for row in range(strip1.shape[0]):
                pixel1 = int(strip1[row, col_offset])

                # Determine the search window in strip2_wide
                if orientation == 2:
                    # For left orientation, match from right of strip2_wide
                    center_col = strip2_wide.shape[1] - depth + col_offset
                else:
                    # For right orientation, match from left of strip2_wide
                    center_col = col_offset

                # Search in a tolerance window around the expected position
                found_match = False
                for dc in range(-tolerance, tolerance + 1):
                    search_col = center_col + dc
                    if 0 <= search_col < strip2_wide.shape[1]:
                        pixel2 = int(strip2_wide[row, search_col])
                        if pixel1 == pixel2:
                            found_match = True
                            break

                if not found_match:
                    total_mismatch += 1

        mismatch_fraction = total_mismatch / max(1, total_positions)

    # Proximity score: (#matches - #misses)/N in [-1, 1]
    matches = max(0, (max(1, total_positions) - total_mismatch))
    misses = total_mismatch
    proximity_score = (matches - misses) / max(1, total_positions)

    # Combine base mismatch with proximity bonus/penalty
    final = mismatch_fraction - (PROXIMITY_WEIGHT_EDGE * proximity_score)
    # Ensure final is within [0, 1]
    final = max(0.0, min(1.0, final))

    return float(final)


# --- Combined Calculator ---


class SimilarityCalculator:
    """
    Weighted combination of similarity functions using preprocessed piece types.

    """

    def __init__(self):
        # Read weights from module-level constants
        self.w_color = WEIGHT_COLOR
        self.w_gradient = WEIGHT_GRADIENT
        self.w_histogram = WEIGHT_HISTOGRAM
        self.w_edge = WEIGHT_EDGE
        self.w_contour = WEIGHT_CONTOUR
        self.w_texture = WEIGHT_TEXTURE

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
                e1, e2, orientation, EDGE_DEPTH, PROXIMITY_TOLERANCE
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
