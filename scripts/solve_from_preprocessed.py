#!/usr/bin/env python3
"""
Solver Script - Solve puzzles from preprocessed outputs.

Notes:
    - Similarity weights are configured centrally in `utils/similarity.py`.
    - Use this script to run greedy/genetic solvers over preprocessed tiles.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import argparse
import numpy as np
from tqdm import tqdm

from utils.piece_loader import PieceLoader
from solvers.solver import solve
from utils.image_utils import merge_pieces, save_image
from utils.similarity import SimilarityCalculator


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
        # Load ALL preprocessed types
        pieces_dict = loader.load_all_types(puzzle_id)

        if "original" not in pieces_dict:
            raise ValueError(f"Missing original pieces for puzzle {puzzle_id}")

        rows, cols = loader.rows, loader.cols

        # Solve using all preprocessed types
        arrangement = solve(
            pieces_dict=pieces_dict,
            rows=rows,
            cols=cols,
            method=method,
            similarity=similarity_calc,
            **solver_kwargs,
        )

        # Reconstruct final image using ORIGINAL pieces
        result = merge_pieces(pieces_dict["original"], arrangement, rows)
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
        "-g",
        "--grid-size",
        type=int,
        choices=[2, 4, 8],
        help="Grid size (2, 4 or 8). If not provided, the grid will be inferred from the directory name (must contain '2x2','4x4', or '8x8').",
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
    parser.add_argument("--generations", type=int, default=300, help="GA generations")
    parser.add_argument(
        "--population", type=int, default=300, help="GA population size"
    )
    # Small, high-impact GA options
    parser.add_argument(
        "--tournament-k",
        type=int,
        default=3,
        help="Tournament size for selection (k=1 disables)",
    )
    parser.add_argument(
        "--mutation-rate",
        type=float,
        default=0.1,
        help="Per-child mutation probability",
    )
    parser.add_argument(
        "--mutation-swaps",
        type=int,
        default=1,
        help="Number of random swaps in mutation",
    )
    parser.add_argument(
        "--local-iters",
        type=int,
        default=30,
        help="Local improvement swap attempts per child",
    )
    parser.add_argument(
        "--simple-names",
        action="store_true",
        help="Save solved images with simple sequential names: 0.png,1.png,...",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Start index when using --simple-names (default: 0)",
    )

    # NOTE: Similarity weights are configured centrally in utils/similarity.py
    # and are NOT passed via CLI anymore. Edit the constants there to tune
    # behavior: WEIGHT_COLOR, WEIGHT_GRADIENT, WEIGHT_HISTOGRAM,
    # WEIGHT_EDGE, WEIGHT_CONTOUR, WEIGHT_TEXTURE

    args = parser.parse_args()

    # Setup
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Treat -d as the exact tiles directory; require explicit grid-size or it must be
    # inferable from the directory name (no parent-directory guessing).
    grid_size = None
    if args.grid_size:
        grid_size = f"{args.grid_size}x{args.grid_size}"
    else:
        for g in ["2x2", "4x4", "8x8"]:
            if g in data_dir.name:
                grid_size = g
                break
    if grid_size is None:
        print(f"Error: Could not determine grid size from {data_dir.name}")
        print(
            "Provide --grid-size or set the directory name to include '2x2','4x4' or '8x8'."
        )
        return

    # Initialize loader
    try:
        loader = PieceLoader(str(data_dir), grid_size)
    except Exception as e:
        print(f"Error initializing PieceLoader: {e}")
        return

    # Create similarity calculator (reads weights from utils/similarity.py)
    similarity_calc = SimilarityCalculator()

    # Solver kwargs
    solver_kwargs = {
        "generations": args.generations,
        "population_size": args.population,
        "tournament_k": args.tournament_k,
        "mutation_rate": args.mutation_rate,
        "mutation_swaps": args.mutation_swaps,
        "local_iters": args.local_iters,
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
    print(f"\nSimilarity weights are read from utils/similarity.py constants")
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
    idx = args.start_index
    for pid in tqdm(puzzle_ids, desc="Solving"):
        if args.simple_names:
            filename = f"{idx}.png"
            idx += 1
        else:
            filename = f"{grid_size}_puzzle_{pid:03d}_solved.png"

        output_path = output_dir / filename
        if solve_single(
            loader, pid, output_path, args.method, similarity_calc, **solver_kwargs
        ):
            success_count += 1

    print(f"\n✓ Successfully solved {success_count}/{len(puzzle_ids)} puzzles")
    print(f"Results saved to: {output_dir}/")


if __name__ == "__main__":
    main()
