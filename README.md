# Jigsaw Puzzle Solver

Advanced jigsaw puzzle solver using template matching, SSIM (Structural Similarity Index), and intelligent preprocessing.

## Features

- **Advanced Preprocessing**: Bilateral filtering + CLAHE + unsharp masking
- **Template Matching**: SSIM-based piece-to-reference matching
- **2x2 Exact Solver**: Exhaustive seam cost minimization
- **ID Mismatch Detection**: Automatically corrects mislabeled pieces
- **High Accuracy**: 95%+ SSIM on 2x2, 91%+ on 4x4, 83%+ on 8x8

## Quick Start

```bash
conda activate cv
python scripts/solve.py data/ -o results/
```

## Usage

### Complete Pipeline

```bash
python scripts/solve.py <input_dir> -o <output_dir>
```

Options:

- `--ssim-threshold`: Minimum SSIM for solved (default: 0.6)
- `--skip-preprocessing`: Skip preprocessing stage
- `--skip-cropping`: Skip cropping stage
- `--only-solve`: Only run solver on cropped data

### Quick Solve (Pre-cropped)

```bash
python scripts/solve_quick.py <cropped_dir> <correct_dir> -o <output_dir>
```

Options:

- `--puzzle-type`: Process only 2x2, 4x4, 8x8, or all
- `--puzzle-id`: Solve specific puzzle by ID

### Python API

```python
from solvers import PuzzleSolver
from utils import preprocess_pipeline, crop_puzzle_into_grid
import cv2

# Preprocess
img = cv2.imread('puzzle.jpg')
enhanced = preprocess_pipeline(img)

# Crop
crop_puzzle_into_grid(enhanced, grid_size=4, puzzle_id=1, output_dir='pieces/')

# Solve
solver = PuzzleSolver(
    dataset_path='pieces/',
    correct_path='correct/',
    output_path='solved/'
)
solver.process_all()
```

## Dataset Structure

Input:

```
data/
  puzzle_2x2/
  puzzle_4x4/
  puzzle_8x8/
  correct/
```

Output:

```
output/
  cropped/
    puzzle_2x2/
    puzzle_4x4/
    puzzle_8x8/
    correct/
  solved/
    puzzle_2x2/
    puzzle_4x4/
    puzzle_8x8/
```

## Algorithm

1. **Preprocessing**: Denoise with bilateral filter → Enhance edges with CLAHE + unsharp mask
2. **Template Matching**: For each position, find piece with highest SSIM to reference region
3. **2x2 Exact Solver**: Try all permutations, minimize seam costs in LAB space
4. **ID Correction**: Auto-detect and fix mislabeled puzzles by testing nearby IDs

## Performance

Tested on 330 puzzles:

| Type | Avg SSIM | Success |
| ---- | -------- | ------- |
| 2x2  | 0.951    | 100%    |
| 4x4  | 0.912    | 100%    |
| 8x8  | 0.835    | 100%    |

## Structure

```
├── solvers/solver.py        # Main solver
├── utils/
│   ├── enhanced_preprocessing.py
│   ├── cropping.py
│   └── image_utils.py
├── scripts/
│   ├── solve.py            # Complete pipeline
│   └── solve_quick.py      # Quick solver
└── data/                   # Input puzzles
```

## Requirements

```bash
pip install -r requirements.txt
```

- Python 3.8+
- opencv-python
- numpy
- scikit-image
- matplotlib
