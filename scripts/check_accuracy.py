#!/usr/bin/env python3
"""
Smart Accuracy Checker for Jigsaw Puzzle Solver

Compares original puzzle images with solved puzzle images and calculates accuracy.
Features:
- Exact position matching (100% credit)
- Neighborhood matching with partial credit (decreasing with distance)
- Perceptual similarity using SSIM and histogram comparison
- Configurable tolerance and neighborhood size

Usage:
    python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4
    python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4 --neighborhood 2 --partial-credit 0.5
"""

import argparse
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict
from skimage.metrics import structural_similarity as ssim
from dataclasses import dataclass


@dataclass
class MatchResult:
    """Result of matching a single piece."""

    source_position: int
    best_match_position: int
    best_match_score: float
    is_exact: bool
    distance: int  # Manhattan distance from correct position
    credit: float  # Accuracy credit (0.0 to 1.0)


def load_image(path: Path) -> np.ndarray:
    """Load an image in RGB format."""
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Failed to load image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def split_into_tiles(image: np.ndarray, grid_size: int) -> List[np.ndarray]:
    """Split image into grid_size x grid_size tiles."""
    h, w = image.shape[:2]
    tile_h = h // grid_size
    tile_w = w // grid_size

    tiles = []
    for row in range(grid_size):
        for col in range(grid_size):
            y_start = row * tile_h
            y_end = y_start + tile_h
            x_start = col * tile_w
            x_end = x_start + tile_w
            tile = image[y_start:y_end, x_start:x_end].copy()
            tiles.append(tile)

    return tiles


def compute_tile_similarity(tile1: np.ndarray, tile2: np.ndarray) -> float:
    """
    Compute similarity between two tiles using multiple metrics.
    Returns a score from 0 (different) to 1 (identical).
    """
    if tile1.shape != tile2.shape:
        return 0.0

    # 1. SSIM (Structural Similarity Index) - perceptual similarity
    # Convert to grayscale for SSIM
    gray1 = cv2.cvtColor(tile1, cv2.COLOR_RGB2GRAY)
    gray2 = cv2.cvtColor(tile2, cv2.COLOR_RGB2GRAY)

    # Compute SSIM with smaller window for small tiles
    win_size = min(7, min(gray1.shape[0], gray1.shape[1]))
    if win_size % 2 == 0:
        win_size -= 1
    win_size = max(3, win_size)

    ssim_score = ssim(gray1, gray2, win_size=win_size, data_range=255)

    # 2. Color histogram similarity
    hist1 = [cv2.calcHist([tile1], [i], None, [32], [0, 256]) for i in range(3)]
    hist2 = [cv2.calcHist([tile2], [i], None, [32], [0, 256]) for i in range(3)]

    hist_scores = []
    for h1, h2 in zip(hist1, hist2):
        cv2.normalize(h1, h1)
        cv2.normalize(h2, h2)
        # Use correlation for histogram comparison
        score = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
        hist_scores.append(score)

    hist_score = np.mean(hist_scores)

    # 3. Mean Absolute Error (normalized)
    mae = np.mean(np.abs(tile1.astype(float) - tile2.astype(float))) / 255.0
    mae_score = 1.0 - mae

    # Combine scores with weights
    # SSIM is most important for perceptual similarity
    combined_score = 0.5 * ssim_score + 0.3 * hist_score + 0.2 * mae_score

    return max(0.0, min(1.0, combined_score))


def find_best_match(
    source_tile: np.ndarray,
    target_tiles: List[np.ndarray],
    similarity_threshold: float = 0.7,
) -> Tuple[int, float]:
    """
    Find the best matching tile in target tiles.
    Returns (best_index, similarity_score).
    """
    best_idx = -1
    best_score = 0.0

    for idx, target_tile in enumerate(target_tiles):
        score = compute_tile_similarity(source_tile, target_tile)
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx, best_score


def calculate_manhattan_distance(pos1: int, pos2: int, grid_size: int) -> int:
    """Calculate Manhattan distance between two positions in the grid."""
    row1, col1 = pos1 // grid_size, pos1 % grid_size
    row2, col2 = pos2 // grid_size, pos2 % grid_size
    return abs(row1 - row2) + abs(col1 - col2)


def calculate_credit(
    distance: int,
    similarity: float,
    max_neighborhood: int,
    partial_credit_factor: float,
    similarity_threshold: float = 0.7,
    relative_bonus: float = 0.0,
) -> float:
    """
    Calculate accuracy credit based on distance and similarity.

    Args:
        distance: Manhattan distance from correct position
        similarity: Tile similarity score (0-1)
        max_neighborhood: Maximum distance to give partial credit
        partial_credit_factor: Base partial credit for neighbors
        similarity_threshold: Minimum similarity to count as match
        relative_bonus: Extra credit for correct relative positioning

    Returns:
        Credit value from 0.0 to 1.0
    """
    # Require minimum similarity threshold
    if similarity < similarity_threshold:
        # Still give some credit if pieces are correctly positioned relative to neighbors
        return min(
            relative_bonus, 0.3
        )  # Cap relative bonus at 30% if similarity is low

    # Exact position
    if distance == 0:
        return 1.0

    # Outside neighborhood
    if distance > max_neighborhood:
        # Still give credit for correct relative positioning even if far from correct spot
        return min(relative_bonus * similarity, 0.4)  # Cap at 40%

    # Partial credit decreases with distance
    # distance=1: partial_credit_factor
    # distance=2: partial_credit_factor * 0.5
    # distance=3: partial_credit_factor * 0.33, etc.
    credit = partial_credit_factor / distance

    # Also scale by similarity
    credit *= similarity

    # Add bonus for correct relative positioning
    credit += relative_bonus * 0.5  # Relative bonus worth 50% when in neighborhood

    return min(1.0, credit)


def check_relative_positioning(
    source_idx: int,
    best_match_idx: int,
    match_results: List[MatchResult],
    grid_size: int,
) -> float:
    """
    Check if a piece's neighbors are also correctly positioned relative to it.
    Returns a bonus score from 0.0 to 1.0 based on how many neighbors are correct.

    Args:
        source_idx: Original position of this piece
        best_match_idx: Where this piece was placed in solved puzzle
        match_results: Results for all pieces so far
        grid_size: Size of the puzzle grid

    Returns:
        Relative positioning bonus (0.0 to 1.0)
    """
    # Get neighbors in original puzzle
    original_row, original_col = source_idx // grid_size, source_idx % grid_size
    solved_row, solved_col = best_match_idx // grid_size, best_match_idx % grid_size

    correct_relative = 0
    total_neighbors = 0

    # Check all 4 directions (up, down, left, right)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dr, dc in directions:
        # Original neighbor position
        orig_neighbor_row = original_row + dr
        orig_neighbor_col = original_col + dc

        # Skip if out of bounds
        if not (
            0 <= orig_neighbor_row < grid_size and 0 <= orig_neighbor_col < grid_size
        ):
            continue

        orig_neighbor_idx = orig_neighbor_row * grid_size + orig_neighbor_col

        # Check if this neighbor has been processed
        if orig_neighbor_idx >= len(match_results):
            continue

        total_neighbors += 1

        # Where the neighbor was placed
        neighbor_solved_idx = match_results[orig_neighbor_idx].best_match_position
        neighbor_solved_row = neighbor_solved_idx // grid_size
        neighbor_solved_col = neighbor_solved_idx % grid_size

        # Check if relative position is maintained
        expected_solved_row = solved_row + dr
        expected_solved_col = solved_col + dc

        if (
            neighbor_solved_row == expected_solved_row
            and neighbor_solved_col == expected_solved_col
        ):
            correct_relative += 1

    if total_neighbors == 0:
        return 0.0

    return correct_relative / total_neighbors


def check_puzzle_accuracy(
    original_image: np.ndarray,
    solved_image: np.ndarray,
    grid_size: int,
    max_neighborhood: int = 1,
    partial_credit_factor: float = 0.6,
    similarity_threshold: float = 0.7,
    verbose: bool = True,
    use_relative_bonus: bool = True,
) -> Dict:
    """
    Check accuracy of solved puzzle with relative positioning awareness.

    Returns dictionary with:
        - exact_matches: number of pieces in exact position
        - partial_matches: number of pieces in neighborhood
        - total_credit: sum of all credits
        - accuracy: percentage (total_credit / total_pieces * 100)
        - match_results: list of MatchResult objects
        - relative_matches: number of pieces with correct relative positioning
    """
    # Split into tiles
    original_tiles = split_into_tiles(original_image, grid_size)
    solved_tiles = split_into_tiles(solved_image, grid_size)

    total_pieces = len(original_tiles)
    match_results = []

    if verbose:
        print(f"\nAnalyzing {total_pieces} pieces ({grid_size}x{grid_size} grid)...")
        print(f"Neighborhood size: {max_neighborhood}")
        print(f"Partial credit factor: {partial_credit_factor}")
        print(f"Similarity threshold: {similarity_threshold}")
        print(
            f"Relative positioning bonus: {'Enabled' if use_relative_bonus else 'Disabled'}\n"
        )

    # First pass: Find best match for each piece
    temp_results = []
    for source_idx, source_tile in enumerate(original_tiles):
        best_idx, similarity = find_best_match(
            source_tile, solved_tiles, similarity_threshold
        )

        distance = calculate_manhattan_distance(source_idx, best_idx, grid_size)
        is_exact = distance == 0

        result = MatchResult(
            source_position=source_idx,
            best_match_position=best_idx,
            best_match_score=similarity,
            is_exact=is_exact,
            distance=distance,
            credit=0.0,  # Will be calculated in second pass
        )
        temp_results.append(result)

    # Second pass: Calculate credit with relative positioning bonus
    relative_bonus_count = 0
    for idx, result in enumerate(temp_results):
        # Check relative positioning
        relative_bonus = 0.0
        if use_relative_bonus:
            relative_bonus = check_relative_positioning(
                result.source_position,
                result.best_match_position,
                temp_results,
                grid_size,
            )
            if relative_bonus > 0.5:  # More than half neighbors correct
                relative_bonus_count += 1

        # Calculate final credit with relative bonus
        credit = calculate_credit(
            result.distance,
            result.best_match_score,
            max_neighborhood,
            partial_credit_factor,
            similarity_threshold,
            relative_bonus,
        )

        # Update result with final credit
        final_result = MatchResult(
            source_position=result.source_position,
            best_match_position=result.best_match_position,
            best_match_score=result.best_match_score,
            is_exact=result.is_exact,
            distance=result.distance,
            credit=credit,
        )
        match_results.append(final_result)

        if verbose and (result.is_exact or credit > 0):
            row, col = (
                result.source_position // grid_size,
                result.source_position % grid_size,
            )
            status = "EXACT" if result.is_exact else f"NEAR(d={result.distance})"
            rel_info = f" rel={relative_bonus:.2f}" if relative_bonus > 0 else ""
            print(
                f"Piece [{row},{col}] pos={result.source_position:2d}: {status} "
                f"match={result.best_match_position:2d} sim={result.best_match_score:.3f} "
                f"credit={credit:.3f}{rel_info}"
            )

    # Calculate statistics
    exact_matches = sum(1 for r in match_results if r.is_exact)
    partial_matches = sum(1 for r in match_results if r.credit > 0 and not r.is_exact)
    total_credit = sum(r.credit for r in match_results)
    accuracy = (total_credit / total_pieces * 100) if total_pieces > 0 else 0.0

    return {
        "exact_matches": exact_matches,
        "partial_matches": partial_matches,
        "relative_bonus_count": relative_bonus_count,
        "total_pieces": total_pieces,
        "total_credit": total_credit,
        "accuracy": accuracy,
        "match_results": match_results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Smart accuracy checker for jigsaw puzzle solver"
    )

    # Required arguments
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="Input directory with original puzzle images",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        required=True,
        help="Output directory with solved puzzle images",
    )
    parser.add_argument(
        "-g",
        "--grid-size",
        type=int,
        required=True,
        choices=[2, 4, 8],
        help="Grid size (2, 4, or 8)",
    )

    # Optional arguments
    parser.add_argument(
        "--neighborhood",
        type=int,
        default=1,
        help="Maximum Manhattan distance for partial credit (default: 1)",
    )
    parser.add_argument(
        "--partial-credit",
        type=float,
        default=0.6,
        help="Base partial credit factor for neighboring pieces (default: 0.6)",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.7,
        help="Minimum similarity score to count as match (default: 0.7)",
    )
    parser.add_argument("--puzzle-id", type=int, help="Check specific puzzle ID only")
    parser.add_argument(
        "--ext", default="png", help="Image file extension (default: png)"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress per-piece output"
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return

    if not output_dir.exists():
        print(f"Error: Output directory not found: {output_dir}")
        return

    # Get list of images to compare
    input_files = sorted(input_dir.glob(f"*.{args.ext}"))
    # Collect output files with multiple possible extensions
    output_files = {}
    for ext in ["png", "jpg", "jpeg"]:
        for f in output_dir.glob(f"*.{ext}"):
            output_files[f.name] = f

    if args.puzzle_id is not None:
        # Filter for specific puzzle ID
        input_files = [
            f
            for f in input_files
            if f"_{args.puzzle_id:03d}_" in f.name
            or f.name.startswith(f"{args.puzzle_id}.")
        ]

    if not input_files:
        print(f"No input images found in {input_dir}")
        return

    print(f"{'='*70}")
    print(f"Puzzle Accuracy Check")
    print(f"{'='*70}")
    print(f"Checking {len(input_files)} puzzles...")
    print()

    # Process each puzzle
    all_results = []

    for input_file in input_files:
        # Try to find corresponding output file
        output_file = None

        # Extract base name without extension from input
        input_base = input_file.stem  # filename without extension

        # Try exact name match (different extension OK)
        for ext in ["png", "jpg", "jpeg"]:
            candidate = f"{input_base}.{ext}"
            if candidate in output_files:
                output_file = output_files[candidate]
                break

        if output_file is None:
            # Try numbered format (0.png, 1.png, etc.)
            # Extract first number from filename
            import re

            match = re.search(r"^(\d+)", input_base)
            if match:
                puzzle_num = match.group(1)
                for ext in ["png", "jpg", "jpeg"]:
                    candidate = f"{puzzle_num}.{ext}"
                    if candidate in output_files:
                        output_file = output_files[candidate]
                        break

        if output_file is None:
            continue

        try:
            # Load images
            original = load_image(input_file)
            solved = load_image(output_file)

            # Check accuracy
            result = check_puzzle_accuracy(
                original,
                solved,
                args.grid_size,
                max_neighborhood=args.neighborhood,
                partial_credit_factor=args.partial_credit,
                similarity_threshold=args.similarity_threshold,
                verbose=False,  # Always quiet during processing
            )

            all_results.append({"filename": input_file.name, "result": result})

        except Exception as e:
            if not args.quiet:
                print(f"Error processing {input_file.name}: {e}")
            continue

    # Print overall statistics
    if all_results:
        print(f"\n{'='*70}")
        print(f"OVERALL STATISTICS")
        print(f"{'='*70}")

        total_puzzles = len(all_results)
        avg_accuracy = np.mean([r["result"]["accuracy"] for r in all_results])

        print(f"Puzzles checked:       {total_puzzles}")
        print(f"Average accuracy:      {avg_accuracy:.2f}%")
        print(f"{'='*70}")

    else:
        print("\nNo puzzles were successfully checked.")


if __name__ == "__main__":
    main()
