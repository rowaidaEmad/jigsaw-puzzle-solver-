#!/usr/bin/env python3
"""
Generate example images for the frontend showing preprocessing steps.
Creates a visual comparison of: Original -> Upscaled -> Binary -> Edges -> Contours
"""
import os
import cv2
import numpy as np
from upscale import upscale_lanczos_sharp


def process_example(input_path: str, output_dir: str, puzzle_name: str):
    """Process a single puzzle image and generate example outputs."""
    
    # Read the puzzle image
    puzzle = cv2.imread(input_path)
    if puzzle is None:
        print(f"Failed to read {input_path}")
        return
    
    # Take just one tile as example (top-left corner)
    h, w = puzzle.shape[:2]
    # Assume 4x4 grid for now
    N = 4
    tile_h = h // N
    tile_w = w // N
    
    # Extract first tile
    tile = puzzle[0:tile_h, 0:tile_w]
    tile_rgb = cv2.cvtColor(tile, cv2.COLOR_BGR2RGB)
    
    # 1. ORIGINAL (resize to consistent size)
    original = cv2.resize(tile, (300, 300))
    cv2.imwrite(os.path.join(output_dir, f"{puzzle_name}_1_original.jpg"), original, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 2. UPSCALED
    tile_upscaled = upscale_lanczos_sharp(tile_rgb, scale_factor=2)
    upscaled_bgr = cv2.cvtColor(tile_upscaled, cv2.COLOR_RGB2BGR)
    upscaled_resized = cv2.resize(upscaled_bgr, (300, 300))
    cv2.imwrite(os.path.join(output_dir, f"{puzzle_name}_2_upscaled.jpg"), upscaled_resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 3. BINARY (grayscale + threshold)
    tile_gray = cv2.cvtColor(upscaled_bgr, cv2.COLOR_BGR2GRAY)
    tile_prep = cv2.medianBlur(tile_gray, 3)
    tile_binary = cv2.adaptiveThreshold(
        tile_prep, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    tile_binary = cv2.morphologyEx(tile_binary, cv2.MORPH_OPEN, kernel, iterations=1)
    tile_binary = cv2.morphologyEx(tile_binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary_resized = cv2.resize(tile_binary, (300, 300))
    cv2.imwrite(os.path.join(output_dir, f"{puzzle_name}_3_binary.jpg"), binary_resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 4. EDGES (Canny)
    edges = cv2.Canny(tile_prep, 40, 50)
    edges_resized = cv2.resize(edges, (300, 300))
    cv2.imwrite(os.path.join(output_dir, f"{puzzle_name}_4_edges.jpg"), edges_resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    # 5. CONTOURS
    contours, _ = cv2.findContours(tile_binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_img = np.zeros_like(tile_binary)
    if contours:
        main_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(contour_img, [main_contour], -1, 255, 2)
    contour_resized = cv2.resize(contour_img, (300, 300))
    cv2.imwrite(os.path.join(output_dir, f"{puzzle_name}_5_contours.jpg"), contour_resized, [cv2.IMWRITE_JPEG_QUALITY, 90])
    
    print(f"✓ Generated examples for {puzzle_name}")


def main():
    # Create output directory
    output_dir = "frontend/public/examples"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process multiple examples from each puzzle size
    examples = [
        ("data/puzzle_2x2/0.jpg", "2x2_a"),
        ("data/puzzle_2x2/5.jpg", "2x2_b"),
        ("data/puzzle_4x4/0.jpg", "4x4_a"),
        ("data/puzzle_4x4/10.jpg", "4x4_b"),
        ("data/puzzle_4x4/25.jpg", "4x4_c"),
        ("data/puzzle_8x8/0.jpg", "8x8_a"),
        ("data/puzzle_8x8/15.jpg", "8x8_b"),
        ("data/puzzle_8x8/30.jpg", "8x8_c"),
    ]
    
    for input_path, puzzle_name in examples:
        if os.path.exists(input_path):
            process_example(input_path, output_dir, puzzle_name)
        else:
            print(f"⚠ Skipping {input_path} (not found)")
    
    print(f"\n✨ All examples generated in {output_dir}/")


if __name__ == "__main__":
    main()
