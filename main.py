#!/usr/bin/env python3
"""
Jigsaw Puzzle Solver - Main Entry Point

Usage:
    python main.py solve image.jpg -g 4 -o result.png
    python main.py batch -p 4x4 --method genetic
    python main.py preprocessed -g 4x4 --puzzle-id 0
"""

import argparse
from pathlib import Path

from image_utils import load_image, save_image, split_image, merge_pieces
from piece_loader import PieceLoader
from solver import solve


def cmd_solve(args):
    """Solve a single puzzle image."""
    image = load_image(args.input)
    h, w = image.shape[:2]
    piece_size = h // args.grid

    pieces = split_image(image, piece_size)

    result_order = solve(
        pieces=pieces,
        rows=args.grid,
        cols=args.grid,
        method=args.method,
        generations=args.generations,
        population_size=args.population,
    )

    result = merge_pieces(pieces, result_order, args.grid)
    save_image(result, args.output)
    print(f"Saved: {args.output}")


def cmd_batch(args):
    """Batch process puzzle folders."""
    from tqdm import tqdm

    base = Path(args.base_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    configs = {
        "2x2": ("puzzle_2x2", 112),
        "4x4": ("puzzle_4x4", 56),
        "8x8": ("puzzle_8x8", 28),
    }

    if args.puzzle != "all":
        configs = {args.puzzle: configs[args.puzzle]}

    for key, (folder, piece_size) in configs.items():
        puzzle_dir = base / folder
        if not puzzle_dir.exists():
            print(f"Skipping {key}: {puzzle_dir} not found")
            continue

        grid = int(key.split("x")[0])
        success = 0

        for i in tqdm(range(args.num_images), desc=f"{key}"):
            input_path = puzzle_dir / f"{i}.jpg"
            output_path = out / f"{key}_{i}_ans.png"

            if not input_path.exists():
                continue

            try:
                image = load_image(str(input_path))
                pieces = split_image(image, piece_size)
                order = solve(
                    pieces,
                    grid,
                    grid,
                    method=args.method,
                    generations=args.generations,
                    population_size=args.population,
                )
                result = merge_pieces(pieces, order, grid)
                save_image(result, str(output_path))
                success += 1
            except Exception as e:
                print(f"Error {input_path}: {e}")

        print(f"{key}: {success}/{args.num_images}")


def cmd_preprocessed(args):
    """Solve using preprocessed pieces from output folder."""
    loader = PieceLoader(args.output_dir, args.grid)

    if args.puzzle_id is not None:
        puzzle_ids = [args.puzzle_id]
    else:
        puzzle_ids = loader.get_puzzle_ids()
        if not puzzle_ids:
            print("No puzzles found")
            return

    for pid in puzzle_ids:
        try:
            pieces, contours = loader.load_with_contours(pid)
            rows, cols = loader.rows, loader.cols

            order = solve(
                pieces,
                rows,
                cols,
                method=args.method,
                contours=contours,
                generations=args.generations,
                population_size=args.population,
            )

            result = merge_pieces(pieces, order, rows)
            out_path = (
                Path(args.result_dir) / f"{args.grid}_puzzle_{pid:03d}_solved.png"
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)
            save_image(result, str(out_path))
            print(f"Saved: {out_path}")
        except Exception as e:
            print(f"Error puzzle {pid}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Jigsaw Puzzle Solver")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # solve: single image
    p_solve = subparsers.add_parser("solve", help="Solve a single puzzle image")
    p_solve.add_argument("input", help="Input image path")
    p_solve.add_argument("-o", "--output", default="solved.png")
    p_solve.add_argument("-g", "--grid", type=int, default=4)
    p_solve.add_argument(
        "-m", "--method", choices=["greedy", "genetic"], default="genetic"
    )
    p_solve.add_argument("--generations", type=int, default=100)
    p_solve.add_argument("--population", type=int, default=100)

    # batch: process folders
    p_batch = subparsers.add_parser("batch", help="Batch process puzzle folders")
    p_batch.add_argument("-b", "--base-dir", default="data")
    p_batch.add_argument("-o", "--output-dir", default="results")
    p_batch.add_argument(
        "-p", "--puzzle", choices=["2x2", "4x4", "8x8", "all"], default="all"
    )
    p_batch.add_argument("-n", "--num-images", type=int, default=110)
    p_batch.add_argument(
        "-m", "--method", choices=["greedy", "genetic"], default="genetic"
    )
    p_batch.add_argument("--generations", type=int, default=100)
    p_batch.add_argument("--population", type=int, default=100)

    # preprocessed: use output folder pieces
    p_pre = subparsers.add_parser(
        "preprocessed", help="Solve using preprocessed pieces"
    )
    p_pre.add_argument("-d", "--output-dir", default="output")
    p_pre.add_argument("-r", "--result-dir", default="results")
    p_pre.add_argument("-g", "--grid", default="4x4")
    p_pre.add_argument("--puzzle-id", type=int, default=None)
    p_pre.add_argument(
        "-m", "--method", choices=["greedy", "genetic"], default="genetic"
    )
    p_pre.add_argument("--generations", type=int, default=100)
    p_pre.add_argument("--population", type=int, default=100)

    args = parser.parse_args()

    if args.command == "solve":
        cmd_solve(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "preprocessed":
        cmd_preprocessed(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
