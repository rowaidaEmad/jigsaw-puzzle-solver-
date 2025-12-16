"""
Utility for cropping complete puzzle images into individual pieces.
"""

import cv2
import numpy as np
import os
from typing import Tuple, List


def crop_puzzle_into_grid(
    image: np.ndarray,
    grid_size: int,
    puzzle_id: int,
    output_dir: str,
    save_format: str = "jpg",
) -> List[str]:
    """
    Crop a complete puzzle image into NxN grid pieces.

    Args:
        image: Complete puzzle image
        grid_size: N for NxN grid (e.g., 2, 4, 8)
        puzzle_id: ID number for this puzzle
        output_dir: Directory to save cropped pieces
        save_format: Image format (jpg, png)

    Returns:
        List of saved file paths
    """
    h, w = image.shape[:2]

    cell_h = h // grid_size
    cell_w = w // grid_size

    os.makedirs(output_dir, exist_ok=True)
    saved_paths = []

    for row in range(grid_size):
        for col in range(grid_size):
            x1 = col * cell_w
            y1 = row * cell_h
            x2 = x1 + cell_w
            y2 = y1 + cell_h

            piece = image[y1:y2, x1:x2]

            # Save with naming convention: {puzzle_id}_r{row}_c{col}.{format}
            filename = f"{puzzle_id}_r{row}_c{col}.{save_format}"
            filepath = os.path.join(output_dir, filename)

            cv2.imwrite(filepath, piece)
            saved_paths.append(filepath)

    return saved_paths


def crop_dataset_by_folders(
    input_root: str, output_root: str, grid_map: dict = None, save_format: str = "jpg"
) -> dict:
    """
    Crop entire dataset organized by puzzle type folders.

    Expected structure:
    input_root/
        puzzle_2x2/
            100.jpg
            101.jpg
            ...
        puzzle_4x4/
            200.jpg
            ...
        puzzle_8x8/
            300.jpg
            ...

    Args:
        input_root: Root directory containing puzzle type folders
        output_root: Root directory for output
        grid_map: Dictionary mapping folder names to grid sizes
                 Default: {"puzzle_2x2": 2, "puzzle_4x4": 4, "puzzle_8x8": 8}
        save_format: Image format for pieces

    Returns:
        Dictionary with statistics per folder
    """
    from glob import glob

    if grid_map is None:
        grid_map = {"puzzle_2x2": 2, "puzzle_4x4": 4, "puzzle_8x8": 8}

    stats = {}

    for folder_name, grid_size in grid_map.items():
        in_folder = os.path.join(input_root, folder_name)
        out_folder = os.path.join(output_root, folder_name)

        if not os.path.exists(in_folder):
            print(f"Skipping {folder_name} - folder not found")
            continue

        os.makedirs(out_folder, exist_ok=True)

        # Get all images
        image_paths = sorted(
            glob(os.path.join(in_folder, "*.jpg"))
            + glob(os.path.join(in_folder, "*.png"))
        )

        print(
            f"\nProcessing {folder_name} ({grid_size}x{grid_size}) - {len(image_paths)} images"
        )

        processed = 0
        total_pieces = 0

        for img_path in image_paths:
            try:
                # Extract puzzle ID from filename
                basename = os.path.splitext(os.path.basename(img_path))[0]
                puzzle_id = int(basename)

                # Load and crop
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Failed to load: {img_path}")
                    continue

                pieces = crop_puzzle_into_grid(
                    img, grid_size, puzzle_id, out_folder, save_format
                )

                processed += 1
                total_pieces += len(pieces)

                if processed % 10 == 0:
                    print(f"  Processed {processed}/{len(image_paths)}")

            except Exception as e:
                print(f"Error processing {img_path}: {e}")

        stats[folder_name] = {
            "images": processed,
            "pieces": total_pieces,
            "grid_size": grid_size,
        }

        print(f"  Done: {processed} images -> {total_pieces} pieces")

    return stats


def reconstruct_from_pieces(pieces: dict, grid_size: int) -> np.ndarray:
    """
    Reconstruct complete image from dictionary of pieces.

    Args:
        pieces: Dictionary mapping (row, col) to piece image
        grid_size: N for NxN grid

    Returns:
        Reconstructed image
    """
    # Get piece dimensions from first piece
    first_piece = next(iter(pieces.values()))
    piece_h, piece_w = first_piece.shape[:2]

    # Create output canvas
    output = np.zeros((grid_size * piece_h, grid_size * piece_w, 3), dtype=np.uint8)

    # Place each piece
    for (row, col), piece in pieces.items():
        y1 = row * piece_h
        y2 = y1 + piece_h
        x1 = col * piece_w
        x2 = x1 + piece_w

        output[y1:y2, x1:x2] = piece

    return output


def load_puzzle_pieces(folder: str, puzzle_id: int) -> dict:
    """
    Load all pieces for a specific puzzle from a folder.

    Args:
        folder: Folder containing piece images
        puzzle_id: ID of the puzzle to load

    Returns:
        Dictionary mapping (row, col) to piece image
    """
    pieces = {}

    for filename in os.listdir(folder):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        try:
            # Parse filename: {puzzle_id}_r{row}_c{col}.{ext}
            base_name = os.path.splitext(filename)[0]
            parts = base_name.split("_")

            if len(parts) >= 3 and int(parts[0]) == puzzle_id:
                row = int(parts[1][1:])  # Remove 'r' prefix
                col = int(parts[2][1:])  # Remove 'c' prefix

                img_path = os.path.join(folder, filename)
                img = cv2.imread(img_path)

                if img is not None:
                    pieces[(row, col)] = img

        except (ValueError, IndexError):
            continue

    return pieces
