#!/usr/bin/env python3
"""
Preprocessing Script - Generate all processing outputs for puzzle pieces.

Usage:
    python preprocess_puzzles.py -i data/puzzle_4x4 -o output/tiles_4x4 -g 4
    python preprocess_puzzles.py -i data/puzzle_8x8 -o output/tiles_8x8 -g 8 --num-images 50
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
from tqdm import tqdm

from image_utils import load_image, split_image
from preprocessing import preprocess
from upscale import upscale_lanczos_sharp


def process_single_puzzle(
    input_path: Path,
    output_base: Path,
    puzzle_id: int,
    grid_size: int,
    piece_size: int,
):
    """Process one puzzle image and generate all outputs."""

    # Load and split
    image = load_image(str(input_path))
    pieces = split_image(image, piece_size)

    if len(pieces) != grid_size * grid_size:
        print(f"Warning: Expected {grid_size*grid_size} pieces, got {len(pieces)}")
        return False

    # Create output directories
    dirs = {
        "original": output_base / "original",
        "prep": output_base / "prep",
        "upscaled": output_base / "upscaled",
        "binary": output_base / "binary",
        "edges": output_base / "edges",
        "contours": output_base / "contours",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # Process each piece
    for idx, piece in enumerate(pieces):
        row = idx // grid_size
        col = idx % grid_size
        base_name = f"puzzle_{puzzle_id:03d}_r{row}_c{col}.png"

        # 1. Original
        cv2.imwrite(
            str(dirs["original"] / base_name), cv2.cvtColor(piece, cv2.COLOR_RGB2BGR)
        )

        # 2. Preprocessed (denoise + bilateral)
        piece_prep = preprocess(piece, method="full")
        cv2.imwrite(
            str(dirs["prep"] / base_name), cv2.cvtColor(piece_prep, cv2.COLOR_RGB2BGR)
        )

        # 3. Upscaled
        piece_upscaled = upscale_lanczos_sharp(piece_prep, scale_factor=2)
        piece_upscaled_resized = cv2.resize(piece_upscaled, (piece_size, piece_size))
        cv2.imwrite(
            str(dirs["upscaled"] / base_name),
            cv2.cvtColor(piece_upscaled_resized, cv2.COLOR_RGB2BGR),
        )

        # 4. Binary (for contour detection)
        gray = cv2.cvtColor(piece_upscaled_resized, cv2.COLOR_RGB2GRAY)
        gray_prep = cv2.medianBlur(gray, 3)
        binary = cv2.adaptiveThreshold(
            gray_prep, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        cv2.imwrite(str(dirs["binary"] / base_name), binary)

        # 5. Edges (Canny)
        edges = cv2.Canny(gray_prep, 40, 50)
        cv2.imwrite(str(dirs["edges"] / base_name), edges)

        # 6. Contours
        contours, _ = cv2.findContours(
            binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contour_img = np.zeros_like(binary)
        if contours:
            main_contour = max(contours, key=cv2.contourArea)
            cv2.drawContours(contour_img, [main_contour], -1, 255, 2)
        cv2.imwrite(str(dirs["contours"] / base_name), contour_img)

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess puzzle images and generate all outputs"
    )
    parser.add_argument(
        "-i", "--input-dir", required=True, help="Input puzzle directory"
    )
    parser.add_argument(
        "-o", "--output-dir", required=True, help="Output base directory"
    )
    parser.add_argument(
        "-g", "--grid", type=int, required=True, help="Grid size (e.g., 4 for 4x4)"
    )
    parser.add_argument(
        "-n", "--num-images", type=int, default=110, help="Number of images to process"
    )
    parser.add_argument("--start-id", type=int, default=0, help="Starting puzzle ID")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # Calculate piece size based on standard 224x224 images
    piece_sizes = {2: 112, 4: 56, 8: 28}
    piece_size = piece_sizes.get(args.grid)
    if not piece_size:
        print(f"Error: Unsupported grid size {args.grid}. Use 2, 4, or 8.")
        return

    print(f"Preprocessing {args.num_images} puzzles from {input_dir}")
    print(f"Grid: {args.grid}x{args.grid}, Piece size: {piece_size}px")
    print(f"Output: {output_dir}")
    print()

    success_count = 0
    for i in tqdm(
        range(args.start_id, args.start_id + args.num_images), desc="Processing"
    ):
        input_path = input_dir / f"{i}.jpg"

        if not input_path.exists():
            continue

        try:
            if process_single_puzzle(input_path, output_dir, i, args.grid, piece_size):
                success_count += 1
        except Exception as e:
            print(f"\nError processing {input_path}: {e}")

    print(f"\n✓ Successfully preprocessed {success_count}/{args.num_images} puzzles")
    print(f"Output structure:")
    print(f"  {output_dir}/original/     - Original pieces")
    print(f"  {output_dir}/prep/         - Denoised + bilateral filtered")
    print(f"  {output_dir}/upscaled/     - Upscaled pieces")
    print(f"  {output_dir}/binary/       - Binary thresholded")
    print(f"  {output_dir}/edges/        - Canny edges")
    print(f"  {output_dir}/contours/     - Extracted contours")


if __name__ == "__main__":
    main()
