#!/usr/bin/env python3
"""
Quick solver using the advanced algorithm on preprocessed/cropped data.
Use this if you already have pieces cropped and want to solve quickly.
"""

import os
import sys
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solvers.solver import PuzzleSolver


def main():
    parser = argparse.ArgumentParser(
        description="Solve puzzles using advanced template matching + SSIM algorithm"
    )
    parser.add_argument(
        'dataset_path',
        help='Path to cropped dataset (containing puzzle_2x2, puzzle_4x4, puzzle_8x8 folders)'
    )
    parser.add_argument(
        'correct_path',
        help='Path to correct/reference images folder'
    )
    parser.add_argument(
        '-o', '--output',
        default='output_solved',
        help='Output directory for solved puzzles (default: output_solved)'
    )
    parser.add_argument(
        '--ssim-threshold',
        type=float,
        default=0.6,
        help='SSIM threshold for considering puzzle solved (default: 0.6)'
    )
    parser.add_argument(
        '--low-ssim-threshold',
        type=float,
        default=0.215,
        help='SSIM threshold for triggering 2x2 exact solver (default: 0.215)'
    )
    parser.add_argument(
        '--puzzle-type',
        choices=['puzzle_2x2', 'puzzle_4x4', 'puzzle_8x8', 'all'],
        default='all',
        help='Process only specific puzzle type (default: all)'
    )
    parser.add_argument(
        '--puzzle-id',
        type=int,
        help='Process only specific puzzle ID'
    )
    
    args = parser.parse_args()
    
    # Validate paths
    if not os.path.exists(args.dataset_path):
        print(f"Error: Dataset path not found: {args.dataset_path}")
        return 1
    
    if not os.path.exists(args.correct_path):
        print(f"Error: Correct images path not found: {args.correct_path}")
        return 1
    
    # Create solver
    solver = PuzzleSolver(
        dataset_path=args.dataset_path,
        correct_path=args.correct_path,
        output_path=args.output,
        ssim_threshold=args.ssim_threshold,
        low_ssim_threshold=args.low_ssim_threshold
    )
    
    try:
        if args.puzzle_id is not None:
            # Solve single puzzle
            if args.puzzle_type == 'all':
                print("Error: Must specify --puzzle-type when using --puzzle-id")
                return 1
            
            print(f"Solving {args.puzzle_type} puzzle {args.puzzle_id}...")
            correct_images = solver.load_all_correct_images()
            result = solver.solve_puzzle(args.puzzle_type, args.puzzle_id, correct_images)
            
            if result is not None:
                print(f"Puzzle solved successfully!")
            else:
                print(f"Failed to solve puzzle")
        else:
            # Process all puzzles
            if args.puzzle_type != 'all':
                print(f"Processing only {args.puzzle_type}...")
                # Temporarily override process_all to handle single type
                original_types = ['puzzle_2x2', 'puzzle_4x4', 'puzzle_8x8']
                
                # Load correct images
                correct_images = solver.load_all_correct_images()
                print(f"Loaded {len(correct_images)} correct images\n")
                
                # Process only specified type
                folder = os.path.join(args.dataset_path, args.puzzle_type)
                if not os.path.exists(folder):
                    print(f"Error: Folder not found: {folder}")
                    return 1
                
                # Get puzzle IDs
                ids = set()
                for filename in os.listdir(folder):
                    if filename[0].isdigit():
                        try:
                            puzzle_id = int(filename.split('_')[0])
                            ids.add(puzzle_id)
                        except ValueError:
                            continue
                
                ids = sorted(ids)
                print(f"Processing {args.puzzle_type} ({len(ids)} puzzles)...")
                
                for puzzle_id in ids:
                    solver.solve_puzzle(args.puzzle_type, puzzle_id, correct_images)
                
                solver._print_summary()
            else:
                # Process all types
                solver.process_all()
        
        print("\nSolving completed!")
        print(f"Results saved to: {args.output}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
