# Preprocessing & Solving Scripts

Two standalone scripts for a clean preprocessing → solving pipeline.

## 1. Preprocessing Script

**`preprocess_puzzles.py`** - Splits puzzles and generates all processing outputs.

### Usage

```bash
# Preprocess 4x4 puzzles
python3 preprocess_puzzles.py -i data/puzzle_4x4 -o output/tiles_4x4 -g 4

# Preprocess first 50 8x8 puzzles
python3 preprocess_puzzles.py -i data/puzzle_8x8 -o output/tiles_8x8 -g 8 -n 50

# Preprocess puzzles 10-20
python3 preprocess_puzzles.py -i data/puzzle_2x2 -o output/tiles_2x2 -g 2 --start-id 10 -n 10
```

### Output Structure

Creates 6 subdirectories per grid size:
```
output/tiles_4x4/
├── original/     - Original split pieces
├── prep/         - Denoised + bilateral filtered
├── upscaled/     - Upscaled 2x then resized back
├── binary/       - Adaptive threshold + morphology
├── edges/        - Canny edge detection
└── contours/     - Main contour extracted
```

Each file named: `puzzle_XXX_rY_cZ.png`

### Options

- `-i, --input-dir` : Input puzzle folder
- `-o, --output-dir` : Output base directory
- `-g, --grid` : Grid size (2, 4, or 8)
- `-n, --num-images` : Number of images to process (default: 110)
- `--start-id` : Starting puzzle ID (default: 0)

---

## 2. Solver Script

**`solve_from_preprocessed.py`** - Solves puzzles from preprocessed data with configurable weights.

### Usage

```bash
# Solve a single puzzle
python3 solve_from_preprocessed.py -d output/tiles_4x4 -o results --puzzle-id 0

# Solve all preprocessed puzzles
python3 solve_from_preprocessed.py -d output/tiles_4x4 -o results --all

# Solve puzzles 0-9 with custom weights
python3 solve_from_preprocessed.py -d output/tiles_8x8 -o results --all --start 0 --end 10 \
    --weight-color 2.0 --weight-contour 0.8 --weight-gradient 0.5

# Use greedy method instead of genetic
python3 solve_from_preprocessed.py -d output/tiles_4x4 -o results --all --method greedy

# Tune genetic algorithm parameters
python3 solve_from_preprocessed.py -d output/tiles_4x4 -o results --puzzle-id 5 \
    --generations 200 --population 150
```

### Similarity Weights (tunable)

| Flag | Default | Description |
|------|---------|-------------|
| `--weight-color` | 1.0 | Color SSD (edge matching) |
| `--weight-gradient` | 0.5 | Gradient compatibility (MGC) |
| `--weight-histogram` | 0.2 | Color histogram similarity |
| `--weight-edge` | 0.3 | Sobel edge gradients |
| `--weight-contour` | 0.2 | Contour image matching |
| `--weight-texture` | 0.1 | Laplacian texture variance |

### Other Options

- `--color-depth N` : Compare N rows/cols at edges (default: 2)
- `--no-lab` : Use RGB instead of LAB color space
- `--method {greedy,genetic}` : Solver method (default: genetic)
- `--generations N` : GA generations (default: 100)
- `--population N` : GA population size (default: 100)

---

## Complete Pipeline Example

```bash
# 1. Preprocess all 4x4 puzzles
python3 preprocess_puzzles.py -i data/puzzle_4x4 -o output/tiles_4x4 -g 4 -n 110

# 2. Solve with default weights
python3 solve_from_preprocessed.py -d output/tiles_4x4 -o results --all

# 3. Re-solve with emphasis on contours and color
python3 solve_from_preprocessed.py -d output/tiles_4x4 -o results_contour \
    --all --weight-color 2.0 --weight-contour 1.0 --weight-gradient 0.3

# 4. Compare results
ls results/
ls results_contour/
```

---

## Tips

### Preprocessing
- Takes ~0.5s per 4x4 puzzle, ~2s per 8x8 puzzle
- Disk usage: ~200-500KB per piece depending on grid size
- Run once, solve many times with different weights

### Solving
- **Greedy**: Fast (< 1s), good for testing weights
- **Genetic**: Better quality (1-5s), tune generations for accuracy vs speed
- Increase `--weight-color` for cleaner edges
- Increase `--weight-contour` when pieces have distinct shapes
- Use `--color-depth 3` for more robust edge matching

### Weight Tuning Strategy
1. Start with defaults
2. Identify weak matches (check results visually)
3. Increase weights for features that matter (e.g., color for similar textures)
4. Re-run solver with new weights (no need to re-preprocess)
