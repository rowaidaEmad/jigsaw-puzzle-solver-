#!/usr/bin/env python3
"""
Solver Script - Solve puzzles from preprocessed outputs with configurable weights.

Usage:
    python solve_from_preprocessed.py -d output/tiles_4x4 -o results --puzzle-id 0
    python solve_from_preprocessed.py -d output/tiles_8x8 -o results --all --method genetic
    python solve_from_preprocessed.py -d output/tiles_4x4 --puzzle-id 5 --weight-color 2.0 --weight-contour 0.5
"""

import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm

from piece_loader import PieceLoader
from solver import solve
from image_utils import merge_pieces, save_image
from similarity import SimilarityCalculator


def solve_single(
    loader: PieceLoader,
    puzzle_id: int,
    output_path: Path,
    method: str,
    similarity_calc: SimilarityCalculator,
    **solver_kwargs,
):
    """Solve one puzzle using all available preprocessed data."""

    try:
        # Load pieces with contours
        pieces, contours = loader.load_with_contours(puzzle_id, piece_type="original")
        rows, cols = loader.rows, loader.cols

        # Solve
        arrangement = solve(
            pieces=pieces,
            rows=rows,
            cols=cols,
            method=method,
            contours=contours,
            similarity=similarity_calc,
            **solver_kwargs,
        )

        # Merge and save
        result = merge_pieces(pieces, arrangement, rows)
        save_image(result, str(output_path))
        return True

    except Exception as e:
        print(f"Error solving puzzle {puzzle_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Solve puzzles from preprocessed outputs with configurable similarity weights"
    )

    # Input/output
    parser.add_argument(
        "-d",
        "--data-dir",
        required=True,
        help="Preprocessed data directory (e.g., output/tiles_4x4)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="results",
        help="Output directory for solved puzzles",
    )

    # Puzzle selection
    parser.add_argument("--puzzle-id", type=int, help="Specific puzzle ID to solve")
    parser.add_argument(
        "--all", action="store_true", help="Solve all available puzzles"
    )
    parser.add_argument(
        "--start", type=int, default=0, help="Start puzzle ID (with --all)"
    )
    parser.add_argument("--end", type=int, help="End puzzle ID (with --all)")

    # Solver method
    parser.add_argument(
        "-m", "--method", choices=["greedy", "genetic"], default="genetic"
    )
    parser.add_argument("--generations", type=int, default=100, help="GA generations")
    parser.add_argument(
        "--population", type=int, default=100, help="GA population size"
    )

    # Similarity weights
    parser.add_argument(
        "--weight-color", type=float, default=1.0, help="Color SSD weight"
    )
    parser.add_argument(
        "--weight-gradient",
        type=float,
        default=0.5,
        help="Gradient compatibility weight",
    )
    parser.add_argument(
        "--weight-histogram",
        type=float,
        default=0.2,
        help="Histogram similarity weight",
    )
    parser.add_argument(
        "--weight-edge", type=float, default=0.3, help="Edge gradient weight"
    )
    parser.add_argument(
        "--weight-contour", type=float, default=0.2, help="Contour matching weight"
    )
    parser.add_argument(
        "--weight-texture", type=float, default=0.1, help="Texture similarity weight"
    )

    # Color/depth options
    parser.add_argument(
        "--color-depth", type=int, default=2, help="Color comparison depth (rows/cols)"
    )
    parser.add_argument(
        "--no-lab", action="store_true", help="Use RGB instead of LAB color space"
    )

    args = parser.parse_args()

    # Setup
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine grid size from directory name
    grid_size = None
    for g in ["2x2", "4x4", "8x8"]:
        if g in data_dir.name:
            grid_size = g
            break
    if not grid_size:
        print(f"Error: Could not determine grid size from {data_dir.name}")
        print("Expected directory name to contain '2x2', '4x4', or '8x8'")
        return

    # Initialize loader
    loader = PieceLoader(str(data_dir.parent), grid_size)

    # Create similarity calculator with custom weights
    similarity_calc = SimilarityCalculator(
        weight_color=args.weight_color,
        weight_gradient=args.weight_gradient,
        weight_histogram=args.weight_histogram,
        weight_edge=args.weight_edge,
        weight_contour=args.weight_contour,
        weight_texture=args.weight_texture,
        color_depth=args.color_depth,
        use_lab=not args.no_lab,
    )

    # Solver kwargs
    solver_kwargs = {
        "generations": args.generations,
        "population_size": args.population,
    }

    # Print configuration
    print(f"Solver Configuration")
    print(f"====================")
    print(f"Data directory: {data_dir}")
    print(f"Grid size: {grid_size}")
    print(f"Method: {args.method}")
    if args.method == "genetic":
        print(f"  Generations: {args.generations}")
        print(f"  Population: {args.population}")
    print(f"\nSimilarity Weights:")
    print(f"  Color:     {args.weight_color}")
    print(f"  Gradient:  {args.weight_gradient}")
    print(f"  Histogram: {args.weight_histogram}")
    print(f"  Edge:      {args.weight_edge}")
    print(f"  Contour:   {args.weight_contour}")
    print(f"  Texture:   {args.weight_texture}")
    print(f"  Color depth: {args.color_depth}, LAB: {not args.no_lab}")
    print()

    # Determine puzzles to solve
    if args.puzzle_id is not None:
        puzzle_ids = [args.puzzle_id]
    elif args.all:
        available = loader.get_puzzle_ids()
        if not available:
            print(f"Error: No puzzles found in {data_dir}")
            return

        start = args.start
        end = args.end if args.end is not None else max(available) + 1
        puzzle_ids = [pid for pid in available if start <= pid < end]

        if not puzzle_ids:
            print(f"Error: No puzzles in range [{start}, {end})")
            return
    else:
        print("Error: Must specify --puzzle-id or --all")
        parser.print_help()
        return

    print(f"Solving {len(puzzle_ids)} puzzle(s)...\n")

    # Solve puzzles
    success_count = 0
    for pid in tqdm(puzzle_ids, desc="Solving"):
        output_path = output_dir / f"{grid_size}_puzzle_{pid:03d}_solved.png"
        if solve_single(
            loader, pid, output_path, args.method, similarity_calc, **solver_kwargs
        ):
            success_count += 1

    print(f"\n✓ Successfully solved {success_count}/{len(puzzle_ids)} puzzles")
    print(f"Results saved to: {output_dir}/")


if __name__ == "__main__":
    main()
