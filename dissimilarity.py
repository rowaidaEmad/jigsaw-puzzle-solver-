import cv2
import numpy as np
from typing import Tuple


def rgb_to_lab(image: np.ndarray) -> np.ndarray:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    return lab.astype(np.float32)


def edge_ssd(piece1: np.ndarray, piece2: np.ndarray, orientation: str) -> float:
    if orientation == "vertical":
        edge1 = piece1[-1, :, :].astype(np.float32)
        edge2 = piece2[0, :, :].astype(np.float32)
    else:
        edge1 = piece1[:, -1, :].astype(np.float32)
        edge2 = piece2[:, 0, :].astype(np.float32)
    diff = edge1 - edge2
    return np.sum(diff**2)


def edge_ssd_lab(piece1: np.ndarray, piece2: np.ndarray, orientation: str) -> float:
    lab1 = rgb_to_lab(piece1)
    lab2 = rgb_to_lab(piece2)
    if orientation == "vertical":
        edge1 = lab1[-1, :, :]
        edge2 = lab2[0, :, :]
    else:
        edge1 = lab1[:, -1, :]
        edge2 = lab2[:, 0, :]
    diff = edge1 - edge2
    return np.sum(diff**2)


def mgc_dissimilarity(
    piece1: np.ndarray, piece2: np.ndarray, orientation: str
) -> float:
    lab1 = rgb_to_lab(piece1)
    lab2 = rgb_to_lab(piece2)

    if orientation == "vertical":
        p1_inner = lab1[-2, :, :]
        p1_edge = lab1[-1, :, :]
        p2_edge = lab2[0, :, :]
        p2_inner = lab2[1, :, :]
    else:
        p1_inner = lab1[:, -2, :]
        p1_edge = lab1[:, -1, :]
        p2_edge = lab2[:, 0, :]
        p2_inner = lab2[:, 1, :]

    grad1 = p1_edge - p1_inner
    grad2 = p2_inner - p2_edge
    pred_p2 = p1_edge + grad1
    pred_p1 = p2_edge + grad2
    err1 = pred_p2 - p2_edge
    err2 = pred_p1 - p1_edge
    total = np.sum(err1**2) + np.sum(err2**2)
    direct_diff = p1_edge - p2_edge
    total += np.sum(direct_diff**2) * 0.5
    return total


def multi_row_ssd(
    piece1: np.ndarray, piece2: np.ndarray, orientation: str, depth: int = 3
) -> float:
    total = 0.0
    for d in range(depth):
        weight = 1.0 / (d + 1)
        if orientation == "vertical":
            edge1 = piece1[-(d + 1), :, :].astype(np.float32)
            edge2 = piece2[d, :, :].astype(np.float32)
        else:
            edge1 = piece1[:, -(d + 1), :].astype(np.float32)
            edge2 = piece2[:, d, :].astype(np.float32)
        diff = edge1 - edge2
        total += weight * np.sum(diff**2)
    return total


def combined_dissimilarity(
    piece1: np.ndarray, piece2: np.ndarray, orientation: str
) -> float:
    mgc = mgc_dissimilarity(piece1, piece2, orientation)
    multi_ssd = multi_row_ssd(piece1, piece2, orientation)
    return mgc + 0.3 * multi_ssd
