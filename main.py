#!/usr/bin/env python3

import os
import argparse
from pathlib import Path
from tqdm import tqdm

from image_utils import load_image, save_image, split_image, merge_pieces
from solver import solve_puzzle
from comparison import evaluate_accuracy


def solve_single_puzzle(
    input_path: str, output_path: str, image_size: int, piece_size: int, method: str
) -> bool:
    try:
        image = load_image(input_path)
        pieces = split_image(image, piece_size)
        grid_size = image_size // piece_size
        arrangement = solve_puzzle(pieces, grid_size, method=method)
        result = merge_pieces(pieces, arrangement, grid_size)
        save_image(result, output_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def process_puzzle_folder(
    puzzle_dir: str,
    output_dir: str,
    prefix: str,
    image_size: int,
    piece_size: int,
    num_images: int,
    method: str,
) -> int:
    os.makedirs(output_dir, exist_ok=True)
    success_count = 0
    for i in tqdm(range(num_images), desc=f"{prefix}puzzles"):
        input_path = os.path.join(puzzle_dir, f"{i}.jpg")
        output_path = os.path.join(output_dir, f"{prefix}{i}_ans.png")
        if solve_single_puzzle(input_path, output_path, image_size, piece_size, method):
            success_count += 1
    return success_count


def main():
    parser = argparse.ArgumentParser(description="Jigsaw Puzzle Solver")
    parser.add_argument("-b", "--base-dir", type=str, default="data")
    parser.add_argument("-o", "--output-dir", type=str, default="output")
    parser.add_argument("-s", "--image-size", type=int, default=224)
    parser.add_argument("-n", "--num-images", type=int, default=110)
    parser.add_argument(
        "-p", "--only", type=str, choices=["2x2", "4x4", "8x8", "all"], default="all"
    )
    parser.add_argument(
        "-m", "--method", type=str, choices=["brute_force", "greedy"], default="greedy"
    )
    parser.add_argument("-e", "--evaluate", action="store_true")
    parser.add_argument("-f", "--show-failed", action="store_true")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)

    puzzles = [
        ("puzzle_2x2", "2x2_", 112),
        ("puzzle_4x4", "4x4_", 56),
        ("puzzle_8x8", "8x8_", 28),
    ]

    if args.only != "all":
        puzzles = [p for p in puzzles if args.only in p[0]]

    for folder_name, prefix, piece_size in puzzles:
        puzzle_dir = base_dir / folder_name
        if not puzzle_dir.exists():
            continue

        success = process_puzzle_folder(
            str(puzzle_dir),
            str(output_dir),
            prefix,
            args.image_size,
            piece_size,
            args.num_images,
            args.method,
        )
        print(f"{prefix}: {success}/{args.num_images}")

    if args.evaluate:
        correct_dir = base_dir / "correct"
        if correct_dir.exists():
            puzzle_configs = [
                ("2x2_", 112),
                ("4x4_", 56),
                ("8x8_", 28),
            ]
            if args.only != "all":
                puzzle_configs = [p for p in puzzle_configs if args.only in p[0]]

            print("\nEvaluation Results:")
            for prefix, piece_size in puzzle_configs:
                correct, total, accuracy, failed = evaluate_accuracy(
                    str(output_dir),
                    str(correct_dir),
                    prefix,
                    args.num_images,
                    piece_size,
                )
                print(f"{prefix}: {correct}/{total} ({accuracy:.2f}%)")
                if args.show_failed and failed:
                    print(f"  Failed images: {failed}")


if __name__ == "__main__":
    main()
