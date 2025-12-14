import cv2
import numpy as np
from typing import Tuple, Optional


def get_edge(piece: np.ndarray, orientation: int) -> np.ndarray:
    """
    Get edge pixels from a piece.
    orientation: 0=top, 1=bottom, 2=left, 3=right
    """
    if orientation == 0:
        return piece[0, :, :]
    elif orientation == 1:
        return piece[-1, :, :]
    elif orientation == 2:
        return piece[:, 0, :]
    elif orientation == 3:
        return piece[:, -1, :]
    raise ValueError(f"Invalid orientation: {orientation}")


def rgb_to_lab(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 2:
        return image.astype(np.float32)
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    return lab.astype(np.float32)


# --- Individual Similarity Functions ---

def color_ssd(
    piece1: np.ndarray,
    piece2: np.ndarray,
    orientation: int,
    use_lab: bool = True,
    depth: int = 1
) -> float:
    """
    Sum of squared differences between adjacent edges.
    depth: how many rows/cols to compare (1 = edge only)
    """
    if use_lab:
        p1 = rgb_to_lab(piece1)
        p2 = rgb_to_lab(piece2)
    else:
        p1 = piece1.astype(np.float32)
        p2 = piece2.astype(np.float32)

    total = 0.0
    for d in range(depth):
        weight = 1.0 / (d + 1)
        if orientation == 0:  # p2 above p1
            e1 = p1[d, :, :]
            e2 = p2[-(d + 1), :, :]
        elif orientation == 1:  # p2 below p1
            e1 = p1[-(d + 1), :, :]
            e2 = p2[d, :, :]
        elif orientation == 2:  # p2 left of p1
            e1 = p1[:, d, :]
            e2 = p2[:, -(d + 1), :]
        elif orientation == 3:  # p2 right of p1
            e1 = p1[:, -(d + 1), :]
            e2 = p2[:, d, :]
        else:
            raise ValueError(f"Invalid orientation: {orientation}")
        diff = e1 - e2
        total += weight * float(np.sum(diff ** 2))
    return float(total)


def gradient_compatibility(
    piece1: np.ndarray,
    piece2: np.ndarray,
    orientation: int
) -> float:
    """
    Mahalanobis Gradient Compatibility - predicts continuation of gradients.
    """
    p1 = rgb_to_lab(piece1)
    p2 = rgb_to_lab(piece2)

    if orientation == 0:
        p1_inner, p1_edge = p1[1, :, :], p1[0, :, :]
        p2_edge, p2_inner = p2[-1, :, :], p2[-2, :, :]
    elif orientation == 1:
        p1_inner, p1_edge = p1[-2, :, :], p1[-1, :, :]
        p2_edge, p2_inner = p2[0, :, :], p2[1, :, :]
    elif orientation == 2:
        p1_inner, p1_edge = p1[:, 1, :], p1[:, 0, :]
        p2_edge, p2_inner = p2[:, -1, :], p2[:, -2, :]
    elif orientation == 3:
        p1_inner, p1_edge = p1[:, -2, :], p1[:, -1, :]
        p2_edge, p2_inner = p2[:, 0, :], p2[:, 1, :]
    else:
        raise ValueError(f"Invalid orientation: {orientation}")

    grad1 = p1_edge - p1_inner
    grad2 = p2_inner - p2_edge
    pred_p2 = p1_edge + grad1
    pred_p1 = p2_edge + grad2

    err1 = pred_p2 - p2_edge
    err2 = pred_p1 - p1_edge
    return float(np.sum(err1 ** 2) + np.sum(err2 ** 2))


def histogram_similarity(
    piece1: np.ndarray,
    piece2: np.ndarray,
    orientation: int,
    bins: int = 32,
    edge_depth: int = 3
) -> float:
    """
    Compare color histograms of edge regions.
    Returns dissimilarity (lower = more similar).
    """
    if orientation == 0:
        region1 = piece1[:edge_depth, :, :]
        region2 = piece2[-edge_depth:, :, :]
    elif orientation == 1:
        region1 = piece1[-edge_depth:, :, :]
        region2 = piece2[:edge_depth, :, :]
    elif orientation == 2:
        region1 = piece1[:, :edge_depth, :]
        region2 = piece2[:, -edge_depth:, :]
    elif orientation == 3:
        region1 = piece1[:, -edge_depth:, :]
        region2 = piece2[:, :edge_depth, :]
    else:
        raise ValueError(f"Invalid orientation: {orientation}")

    total_dist = 0.0
    for c in range(3):
        h1, _ = np.histogram(region1[:, :, c].flatten(), bins=bins, range=(0, 256))
        h2, _ = np.histogram(region2[:, :, c].flatten(), bins=bins, range=(0, 256))
        h1 = h1.astype(np.float32)
        h2 = h2.astype(np.float32)
        h1 /= h1.sum() + 1e-10
        h2 /= h2.sum() + 1e-10
        total_dist += cv2.compareHist(h1, h2, cv2.HISTCMP_CHISQR)
    return total_dist


def edge_gradient_similarity(
    piece1: np.ndarray,
    piece2: np.ndarray,
    orientation: int
) -> float:
    """
    Compare edge gradients using Sobel operator.
    """
    gray1 = cv2.cvtColor(piece1, cv2.COLOR_RGB2GRAY) if len(piece1.shape) == 3 else piece1
    gray2 = cv2.cvtColor(piece2, cv2.COLOR_RGB2GRAY) if len(piece2.shape) == 3 else piece2

    if orientation in [0, 1]:
        sobel1 = cv2.Sobel(gray1, cv2.CV_64F, 0, 1, ksize=3)
        sobel2 = cv2.Sobel(gray2, cv2.CV_64F, 0, 1, ksize=3)
        if orientation == 0:
            e1, e2 = sobel1[0, :], sobel2[-1, :]
        else:
            e1, e2 = sobel1[-1, :], sobel2[0, :]
    else:
        sobel1 = cv2.Sobel(gray1, cv2.CV_64F, 1, 0, ksize=3)
        sobel2 = cv2.Sobel(gray2, cv2.CV_64F, 1, 0, ksize=3)
        if orientation == 2:
            e1, e2 = sobel1[:, 0], sobel2[:, -1]
        else:
            e1, e2 = sobel1[:, -1], sobel2[:, 0]

    return float(np.sum((e1 - e2) ** 2))


def contour_similarity(
    contour1: Optional[np.ndarray],
    contour2: Optional[np.ndarray],
    orientation: int
) -> float:
    """
    Compare contour images at edges.
    Pass pre-computed contour images.
    """
    if contour1 is None or contour2 is None:
        return 0.0

    if orientation == 0:
        e1, e2 = contour1[0, :], contour2[-1, :]
    elif orientation == 1:
        e1, e2 = contour1[-1, :], contour2[0, :]
    elif orientation == 2:
        e1, e2 = contour1[:, 0], contour2[:, -1]
    elif orientation == 3:
        e1, e2 = contour1[:, -1], contour2[:, 0]
    else:
        raise ValueError(f"Invalid orientation: {orientation}")

    e1 = e1.astype(np.float32)
    e2 = e2.astype(np.float32)
    return float(np.sum((e1 - e2) ** 2))


def texture_similarity(
    piece1: np.ndarray,
    piece2: np.ndarray,
    orientation: int,
    edge_depth: int = 5
) -> float:
    """
    Compare texture using local binary patterns approximation.
    """
    gray1 = cv2.cvtColor(piece1, cv2.COLOR_RGB2GRAY) if len(piece1.shape) == 3 else piece1
    gray2 = cv2.cvtColor(piece2, cv2.COLOR_RGB2GRAY) if len(piece2.shape) == 3 else piece2

    if orientation == 0:
        r1, r2 = gray1[:edge_depth, :], gray2[-edge_depth:, :]
    elif orientation == 1:
        r1, r2 = gray1[-edge_depth:, :], gray2[:edge_depth, :]
    elif orientation == 2:
        r1, r2 = gray1[:, :edge_depth], gray2[:, -edge_depth:]
    elif orientation == 3:
        r1, r2 = gray1[:, -edge_depth:], gray2[:, :edge_depth]
    else:
        raise ValueError(f"Invalid orientation: {orientation}")

    lap1 = cv2.Laplacian(r1, cv2.CV_64F)
    lap2 = cv2.Laplacian(r2, cv2.CV_64F)

    var1 = np.var(lap1)
    var2 = np.var(lap2)
    return float(abs(var1 - var2))


# --- Combined Similarity Function ---

class SimilarityCalculator:
    def __init__(
        self,
        weight_color: float = 1.0,
        weight_gradient: float = 0.5,
        weight_histogram: float = 0.2,
        weight_edge: float = 0.3,
        weight_contour: float = 0.2,
        weight_texture: float = 0.1,
        use_lab: bool = True,
        color_depth: int = 2
    ):
        self.weight_color = weight_color
        self.weight_gradient = weight_gradient
        self.weight_histogram = weight_histogram
        self.weight_edge = weight_edge
        self.weight_contour = weight_contour
        self.weight_texture = weight_texture
        self.use_lab = use_lab
        self.color_depth = color_depth

    def compute(
        self,
        piece1: np.ndarray,
        piece2: np.ndarray,
        orientation: int,
        contour1: Optional[np.ndarray] = None,
        contour2: Optional[np.ndarray] = None
    ) -> float:
        """
        Compute combined dissimilarity score.
        Lower score = better match.
        """
        total = 0.0

        if self.weight_color > 0:
            total += self.weight_color * color_ssd(
                piece1, piece2, orientation,
                use_lab=self.use_lab, depth=self.color_depth
            )

        if self.weight_gradient > 0:
            total += self.weight_gradient * gradient_compatibility(
                piece1, piece2, orientation
            )

        if self.weight_histogram > 0:
            total += self.weight_histogram * histogram_similarity(
                piece1, piece2, orientation
            )

        if self.weight_edge > 0:
            total += self.weight_edge * edge_gradient_similarity(
                piece1, piece2, orientation
            )

        if self.weight_contour > 0 and contour1 is not None and contour2 is not None:
            total += self.weight_contour * contour_similarity(
                contour1, contour2, orientation
            )

        if self.weight_texture > 0:
            total += self.weight_texture * texture_similarity(
                piece1, piece2, orientation
            )

        return total


def dissimilarity(
    piece1: np.ndarray,
    piece2: np.ndarray,
    orientation: int,
    contour1: Optional[np.ndarray] = None,
    contour2: Optional[np.ndarray] = None
) -> float:
    """
    Default dissimilarity function with preset weights.
    orientation: 0=top, 1=bottom, 2=left, 3=right
    """
    calc = SimilarityCalculator()
    return calc.compute(piece1, piece2, orientation, contour1, contour2)
