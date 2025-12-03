"""
Jigsaw Puzzle Solver - Phase 1 Report
Processes a single image (23.jpg) through the 6-stage pipeline
and saves results to output/report/
"""

import os
import cv2
import numpy as np
from upscale import upscale_lanczos_sharp

# Configuration
IMAGE_PATH = "data/puzzle_4x4/23.jpg"
OUTPUT_DIR = "output/report"

# Create output folder
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load image
tile = cv2.imread(IMAGE_PATH)
if tile is None:
    raise FileNotFoundError(f"Could not load {IMAGE_PATH}")

tile_rgb = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB)
print(f"Loaded: {IMAGE_PATH}, Shape: {tile.shape}")

# Stage 1: Original
cv2.imwrite(os.path.join(OUTPUT_DIR, "1_original.png"), tile)
print("Saved: 1_original.png")

# Stage 2: Upscaled
upscaled = upscale_lanczos_sharp(tile_rgb, scale_factor=2)
cv2.imwrite(
    os.path.join(OUTPUT_DIR, "2_upscaled.png"),
    cv2.cvtColor(upscaled, cv2.COLOR_RGB2BGR),
)
print("Saved: 2_upscaled.png")

# Stage 3: Prep (grayscale + median blur)
gray = cv2.cvtColor(upscaled, cv2.COLOR_RGB2GRAY)
prep = cv2.medianBlur(gray, 3)
cv2.imwrite(os.path.join(OUTPUT_DIR, "3_prep.png"), prep)
print("Saved: 3_prep.png")

# Stage 4: Binary (adaptive threshold + morphology)
binary = cv2.adaptiveThreshold(
    prep, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
cv2.imwrite(os.path.join(OUTPUT_DIR, "4_binary.png"), binary)
print("Saved: 4_binary.png")

# Stage 5: Contour
contours, _ = cv2.findContours(
    binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
)
contour_img = np.zeros_like(binary)
if contours:
    main_contour = max(contours, key=cv2.contourArea)
    cv2.drawContours(contour_img, [main_contour], -1, 255, 2)
cv2.imwrite(os.path.join(OUTPUT_DIR, "5_contour.png"), contour_img)
print("Saved: 5_contour.png")

# Stage 6: Edges (Canny)
blurred = cv2.GaussianBlur(prep, (5, 5), 1.4)
edges = cv2.Canny(blurred, 40, 50)
cv2.imwrite(os.path.join(OUTPUT_DIR, "6_edges.png"), edges)
print("Saved: 6_edges.png")

print(f"\nDone! All 6 stages saved to {OUTPUT_DIR}/")
