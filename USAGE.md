# Quick Start Guide

## Running the Puzzle Solver

### Recommended Workflow (2 Steps)

**Step 1: Preprocess** (denoise, enhance, crop)
```bash
conda activate cv
python scripts/preprocess.py data/ -o preprocessed/
```

**Step 2: Solve** (match pieces using advanced algorithm)
```bash
python scripts/solve_quick.py preprocessed/cropped/ preprocessed/cropped/correct/ -o results/
```

This separation allows you to:
- Rerun solving with different parameters without re-preprocessing
- Save preprocessing outputs for different experiments
- Debug each stage independently

### Alternative: Complete Pipeline (All-in-one)

```bash
conda activate cv
python scripts/solve.py data/ -o results/
```

This runs both preprocessing and solving in one command.

### Quick Solve (If you already have cropped pieces)

```bash
conda activate cv
python scripts/solve_quick.py path/to/cropped/pieces/ path/to/correct/ -o output/
```

## Command Options

### preprocess.py (Preprocessing Only)
```bash
python scripts/preprocess.py INPUT_DIR -o OUTPUT_DIR [OPTIONS]

Options:
  -o, --output DIR          Output directory (default: preprocessed)
  --skip-enhancement        Skip denoising and edge enhancement (only crop)
  --skip-cropping          Skip cropping (only enhance)
```

**Example:**
```bash
# Full preprocessing
python scripts/preprocess.py data/ -o preprocessed/

# Only crop (skip enhancement)
python scripts/preprocess.py data/ -o preprocessed/ --skip-enhancement

# Only enhance (skip cropping)
python scripts/preprocess.py data/ -o preprocessed/ --skip-cropping
```

### solve_quick.py (Solver Only)
```bash
python scripts/solve_quick.py DATASET_PATH CORRECT_PATH -o OUTPUT_DIR [OPTIONS]

Options:
  -o, --output DIR              Output directory
  --ssim-threshold FLOAT        SSIM threshold (default: 0.6)
  --low-ssim-threshold FLOAT    Threshold for 2x2 exact solver (default: 0.215)
  --puzzle-type TYPE            puzzle_2x2, puzzle_4x4, puzzle_8x8, or all
  --puzzle-id ID                Process only specific puzzle ID
```

**Examples:**
```bash
# Solve all puzzles
python scripts/solve_quick.py preprocessed/cropped/ preprocessed/cropped/correct/ -o results/

# Solve only 4x4 puzzles
python scripts/solve_quick.py preprocessed/cropped/ preprocessed/cropped/correct/ -o results/ --puzzle-type puzzle_4x4

# Solve single puzzle
python scripts/solve_quick.py preprocessed/cropped/ preprocessed/cropped/correct/ -o results/ --puzzle-type puzzle_4x4 --puzzle-id 42
```

## Testing Examples

### Test the 2-step workflow:
```bash
conda activate cv

# Step 1: Preprocess
python scripts/preprocess.py data/ -o test_prep/

# Step 2: Solve
python scripts/solve_quick.py test_prep/cropped/ test_prep/cropped/correct/ -o test_results/

# Check results
ls test_results/puzzle_2x2/
ls test_results/puzzle_4x4/  
ls test_results/puzzle_8x8/
```

### Test single puzzle type:
```bash
# Preprocess everything first
python scripts/preprocess.py data/ -o prep/

# Solve only 2x2 puzzles
python scripts/solve_quick.py prep/cropped/ prep/cropped/correct/ -o results_2x2/ --puzzle-type puzzle_2x2
```

### Re-solve with different parameters:
```bash
# Preprocessing already done, just re-solve
python scripts/solve_quick.py prep/cropped/ prep/cropped/correct/ -o strict_results/ --ssim-threshold 0.8
python scripts/solve_quick.py prep/cropped/ prep/cropped/correct/ -o loose_results/ --ssim-threshold 0.5
```

### Performance test (measure time):
```bash
time python scripts/preprocess.py data/ -o benchmark_prep/
time python scripts/solve_quick.py benchmark_prep/cropped/ benchmark_prep/cropped/correct/ -o benchmark_results/
```

## Understanding Output

The solver prints progress and statistics:
```
Processing puzzle_4x4 (110 puzzles)...
puzzle_4x4 0: SSIM=0.947
puzzle_4x4 1: SSIM=0.886
...

FINAL STATISTICS
Total puzzles processed: 330
Solved puzzles (SSIM>=0.6): 330
Success rate: 100.0%
Average SSIM: 0.9014
```

**SSIM Score Meaning:**
- `>0.9`: Excellent match
- `0.7-0.9`: Good match
- `0.6-0.7`: Acceptable match
- `<0.6`: Poor match (marked as unsolved)

## Troubleshooting

**Error: ModuleNotFoundError**
```bash
conda activate cv
pip install -r requirements.txt
```

**Low SSIM scores**
- Check that correct reference images exist in data/correct/
- Try adjusting `--ssim-threshold` parameter
- The solver auto-detects ID mismatches

**Out of memory**
- Process one puzzle type at a time using `--puzzle-type`

**Slow preprocessing**
- Skip with `--skip-preprocessing` if data already enhanced
- Skip cropping with `--skip-cropping` if already cropped
