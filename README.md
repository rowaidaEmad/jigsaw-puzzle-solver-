# Jigsaw Puzzle Solver

A modular jigsaw puzzle solver using genetic algorithms with configurable similarity metrics.

## Project Structure

```
jigsaw-puzzle-solver/
├── core/                      # Core puzzle-solving modules
│   ├── similarity.py         # Similarity metrics (color, gradient, edge, etc.)
│   └── piece_loader.py       # Load preprocessed puzzle pieces
├── solvers/                   # Solving algorithms
│   ├── solver.py             # Main solver dispatcher
│   └── genetic.py            # Genetic algorithm with kernel-growing crossover
├── utils/                     # Image processing utilities
│   ├── image_utils.py        # Load, save, split, merge images
│   ├── preprocessing.py      # Denoise and enhance pieces
│   └── upscale.py            # Upscaling utilities
├── scripts/                   # Standalone executable scripts
│   ├── preprocess_puzzles.py # Preprocessing pipeline
│   └── solve_from_preprocessed.py # Solver with configurable weights
├── data/                      # Input puzzle images
│   ├── puzzle_2x2/
│   ├── puzzle_4x4/
│   └── puzzle_8x8/
└── output/                    # Preprocessed pieces and results
    └── tiles_{grid}/
        ├── original/
        ├── prep/             # Denoised + bilateral filter
        ├── upscaled/
        ├── binary/
        ├── edges/
        └── contours/
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### 1. Preprocessing

Generate all preprocessing outputs for puzzle pieces:

```bash
# Process 4x4 puzzles
python scripts/preprocess_puzzles.py -i data/puzzle_4x4 -o output -g 4

# Process 8x8 puzzles with specific count
python scripts/preprocess_puzzles.py -i data/puzzle_8x8 -o output -g 8 --num-images 50

# Process 2x2 puzzles
python scripts/preprocess_puzzles.py -i data/puzzle_2x2 -o output -g 2
```

### 2. Solving

Solve puzzles from preprocessed data:

```bash
# Solve single puzzle with default weights
python scripts/solve_from_preprocessed.py -d output/tiles_4x4 -o results --puzzle-id 0

# Solve all puzzles using genetic algorithm
python scripts/solve_from_preprocessed.py -d output/tiles_8x8 -o results --all --method genetic

# Custom similarity weights
python scripts/solve_from_preprocessed.py -d output/tiles_4x4 --puzzle-id 5 \
    --weight-color 2.0 --weight-gradient 1.5 --weight-contour 0.5

# Fast greedy solving
python scripts/solve_from_preprocessed.py -d output/tiles_2x2 -o results --all --method greedy
```

**Preprocessing Options:**

- `-i, --input-dir`: Input directory with puzzle images
- `-o, --output-dir`: Output base directory (default: `output`)
- `-g, --grid-size`: Grid size (2, 4, or 8)
- `--num-images`: Number of images to process (default: all)

**Solver Options:**

- `-d, --data-dir`: Preprocessed tiles directory
- `-o, --output-dir`: Output directory for results (default: `results`)
- `--puzzle-id`: Solve specific puzzle by ID
- `--all`: Solve all puzzles
- `--method`: Solving method: `greedy` or `genetic` (default: `genetic`)
- `--weight-color`: Color similarity weight (default: 1.0)
- `--weight-gradient`: Gradient compatibility weight (default: 1.0)
- `--weight-histogram`: Histogram similarity weight (default: 1.0)
- `--weight-edge`: Edge gradient similarity weight (default: 1.0)
- `--weight-contour`: Contour matching weight (default: 1.0)
- `--weight-texture`: Texture similarity weight (default: 1.0)

## Algorithm Overview

### Genetic Algorithm

- **Population**: 100 individuals
- **Generations**: 100 iterations
- **Crossover**: Kernel-growing with shared edges, best buddies, and best matches
- **Selection**: Fitness-proportional with elite preservation

### Similarity Metrics

1. **Color SSD**: Sum of squared differences in LAB color space
2. **Gradient Compatibility**: Edge color gradient matching
3. **Histogram Similarity**: Chi-square distance between histograms
4. **Edge Gradient**: Sobel edge gradient comparison
5. **Contour Similarity**: Contour shape matching
6. **Texture Similarity**: Local Binary Pattern comparison

**Note:** By default, the solver looks for puzzle images in the `data/` folder and saves results to `output/`. Make sure your puzzle images are placed in:

- `data/puzzle_2x2/` for 2x2 puzzles
- `data/puzzle_4x4/` for 4x4 puzzles
- `data/puzzle_8x8/` for 8x8 puzzles
