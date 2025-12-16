#!/usr/bin/env python3
"""
Preprocessing pipeline: Denoising, Edge Enhancement, and Cropping.
This script prepares raw puzzle images for solving.
"""

import os
import sys
import argparse
from glob import glob
import cv2
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_preprocessing import preprocess_pipeline
from utils.cropping import crop_dataset_by_folders


def setup_directories(base_output: str) -> dict:
    """Create output directory structure."""
    dirs = {
        "enhanced": os.path.join(base_output, "enhanced"),
        "cropped": os.path.join(base_output, "cropped"),
    }

    for dir_path in dirs.values():
        os.makedirs(dir_path, exist_ok=True)

    return dirs


def preprocess_stage(input_root: str, output_dirs: dict, puzzle_types: list):
    """
    Stage 1 & 2: Denoising and Enhancement
    """
    print("\n" + "=" * 60)
    print("STAGE 1: PREPROCESSING (Denoising + Enhancement)")
    print("=" * 60)

    # Process each puzzle type folder
    for puzzle_type in puzzle_types:
        input_folder = os.path.join(input_root, puzzle_type)

        if not os.path.exists(input_folder):
            print(f"Skipping {puzzle_type} - folder not found")
            continue

        # Get all images
        image_paths = sorted(
            glob(os.path.join(input_folder, "*.jpg"))
            + glob(os.path.join(input_folder, "*.png"))
        )

        if not image_paths:
            print(f"No images found in {puzzle_type}")
            continue

        print(f"\nProcessing {puzzle_type}: {len(image_paths)} images")

        # Create output folders
        enhanced_folder = os.path.join(output_dirs["enhanced"], puzzle_type)
        os.makedirs(enhanced_folder, exist_ok=True)

        # Process each image
        for i, img_path in enumerate(image_paths):
            img = cv2.imread(img_path)
            if img is None:
                continue

            # Apply preprocessing pipeline
            processed = preprocess_pipeline(
                img, apply_denoise=True, apply_enhancement=True
            )

            # Save
            basename = os.path.basename(img_path)
            output_path = os.path.join(enhanced_folder, basename)
            cv2.imwrite(output_path, processed)

            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(image_paths)}")

        print(f"  Completed: {len(image_paths)} images")


def cropping_stage(enhanced_dir: str, cropped_dir: str):
    """
    Stage 3: Cropping images into pieces
    """
    print("\n" + "=" * 60)
    print("STAGE 2: CROPPING INTO PIECES")
    print("=" * 60)

    stats = crop_dataset_by_folders(
        input_root=enhanced_dir,
        output_root=cropped_dir,
        grid_map={"puzzle_2x2": 2, "puzzle_4x4": 4, "puzzle_8x8": 8},
    )


def main():
    parser = argparse.ArgumentParser(
        description="Preprocess puzzle images: denoise, enhance edges, and crop into pieces"
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        help="Input directory containing puzzle folders (puzzle_2x2, puzzle_4x4, puzzle_8x8, correct)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="preprocessed",
        help="Base output directory (default: preprocessed)",
    )
    parser.add_argument(
        "--skip-enhancement",
        action="store_true",
        help="Skip denoising and edge enhancement (only crop)",
    )
    parser.add_argument(
        "--skip-cropping", action="store_true", help="Skip cropping (only enhance)"
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}")
        return 1

    # Setup directories
    output_dirs = setup_directories(args.output)

    puzzle_types = ["puzzle_2x2", "puzzle_4x4", "puzzle_8x8"]

    try:
        if not args.skip_enhancement:
            preprocess_stage(args.input_dir, output_dirs, puzzle_types)
        else:
            print("Skipping enhancement stage")

        if not args.skip_cropping:
            enhanced_source = (
                output_dirs["enhanced"] if not args.skip_enhancement else args.input_dir
            )
            cropping_stage(enhanced_source, output_dirs["cropped"])
        else:
            print("Skipping cropping stage")

        print("\n" + "=" * 60)
        print("PREPROCESSING COMPLETED!")
        print("=" * 60)
        print(f"✓ Enhanced full images: {output_dirs['enhanced']}/")
        print(f"✓ Cropped pieces (preprocessed): {output_dirs['cropped']}/")
        print(f"\n📝 Processing Order:")
        print(f"   1. Denoise + Enhance full images → {output_dirs['enhanced']}/")
        print(f"   2. Crop enhanced images into pieces → {output_dirs['cropped']}/")
        print(
            f"\n💡 Tip: Check {output_dirs['enhanced']}/puzzle_4x4/ to see enhanced full images"
        )
        print(f"\nNext step: Run solver")
        print(
            f"  python scripts/solve_quick.py {output_dirs['cropped']} {args.input_dir}/correct -o results/"
        )

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
