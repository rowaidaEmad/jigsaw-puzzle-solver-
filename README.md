# Jigsaw Puzzle Solver

A jigsaw puzzle solver using computer vision and genetic algorithms to reconstruct square puzzles (2×2, 4×4, 8×8).

🌐 **Live Demo**: [puzzle-crisis.diran.app](https://puzzle-crisis.diran.app)

## Quick Start

Run the complete pipeline for 4×4 puzzles:

```bash
bash run_4.sh
```

Or step by step:

```bash
# Step 1: Preprocessing
python3 scripts/preprocess_puzzles.py -i data/puzzle_4x4 -o output/4x4 -g 4

# Step 2: Solving
python3 scripts/solve_from_preprocessed.py -d output/4x4 --all --output-dir final/4x4 --simple-names

# Step 3: Accuracy Check
python3 scripts/check_accuracy.py -i data/correct -o final/4x4 -g 4 --quiet
```

**Available scripts**: `run_2.sh` (2×2), `run_4.sh` (4×4), `run_8.sh` (8×8)

---

## Overview

This project implements a complete jigsaw puzzle solving pipeline with three main phases:

### **Phase 1: Preprocessing**

Enhances puzzle pieces and extracts visual features for matching.

### **Phase 2: Puzzle Solving (Genetic Algorithm)**

Uses evolutionary optimization to find the best arrangement of pieces.

---

## Pipeline Details

### Phase 1: Preprocessing & Feature Extraction

**Purpose**: Transform raw puzzle images into processed pieces with enhanced features for accurate matching.

#### Steps:

1. **Image Splitting** (`split_image`)

   - Divides the scrambled puzzle into N×N individual tiles
   - **Parameters**:
     - `piece_size`: Calculated as 224/grid_size (e.g., 56px for 4×4)
   - **Impact**: Ensures uniform piece dimensions for consistent processing

2. **Denoising & Preprocessing** (`preprocess`)

   - Applies median blur and bilateral filtering
   - **Method**: `full` - combines noise reduction with edge preservation
   - **Impact**: Reduces noise while maintaining sharp edges critical for matching
   - **Reference**: Bilateral filtering preserves edges while smoothing [Tomasi & Manduchi, 1998]

3. **Upscaling** (`upscale_lanczos_sharp`)

   - Enlarges small pieces using Lanczos interpolation (4× scale)
   - Applies light sharpening to enhance edge clarity
   - **Parameters**:
     - `scale_factor=4`: Increases resolution from 56px to 224px
   - **Impact**: Provides higher resolution for better feature detection and matching
   - **Reference**: Lanczos resampling provides high-quality interpolation [Turkowski, 1990]

4. **Binary Segmentation** (`cv2.adaptiveThreshold`)

   - Separates puzzle piece from background
   - **Method**: Gaussian adaptive thresholding
   - **Parameters**:
     - `blockSize=11`: Local neighborhood size
     - `C=2`: Constant subtracted from mean
   - **Impact**: Handles varying lighting conditions across the puzzle
   - **Morphological operations**: Opening (removes noise) → Closing (fills holes)

5. **Edge Detection** (`cv2.Canny`)

   - Detects edges within each piece
   - **Parameters**:
     - `low_threshold`: 0.55 × median intensity
     - `high_threshold`: 1.0 × median intensity
   - **Impact**: Adaptive thresholds work across different image characteristics
   - **Reference**: Canny edge detection [Canny, 1986]

6. **Contour Extraction** (`cv2.findContours`)
   - Identifies puzzle piece boundaries
   - **Method**: `RETR_EXTERNAL` (only outermost contours)
   - **Filtering**: Keeps contours > 0.2% of image area
   - **Impact**: Focuses on the main piece, ignoring artifacts

**Output Structure**:

```
output/
  ├── original/     - Raw extracted pieces
  ├── prep/         - Denoised pieces
  ├── upscaled/     - High-resolution pieces
  ├── binary/       - Binary masks
  ├── edges/        - Edge maps
  └── contours/     - Extracted contours
```

---

### Phase 2: Puzzle Solving (Genetic Algorithm)

**Purpose**: Find the optimal arrangement of puzzle pieces by treating it as an optimization problem.

#### Algorithm: Genetic Algorithm Approach

**Inspiration**: Mimics natural evolution - maintaining a population of candidate solutions that evolve through selection, crossover, and mutation [Goldberg, 1989].

#### Key Parameters:

1. **Population Size** (`pop_size=100`)

   - Number of candidate solutions maintained per generation
   - **Impact**: Larger population → better exploration but slower convergence
   - Balances diversity vs computational cost

2. **Generations** (`max_generations=100`)

   - Maximum evolutionary iterations
   - **Early stopping**: Terminates if no improvement for 20 generations
   - **Impact**: Prevents wasted computation on converged solutions

3. **Elite Size** (`elite_size=10`)

   - Top solutions preserved unchanged each generation
   - **Impact**: Ensures best solutions aren't lost (elitism strategy)

4. **Mutation Rate** (`mutation_rate=0.15`)
   - Probability of random piece swaps (15%)
   - **Impact**: Maintains diversity, prevents premature convergence
   - Too high → random search; too low → gets stuck in local optima

#### Fitness Function (Similarity Metrics):

The fitness of each arrangement is calculated by summing pairwise similarities between adjacent pieces:

```python
fitness = Σ similarity(piece_i, piece_j) for all adjacent pairs
```

**Similarity Components** (from `utils/similarity.py`):

1. **Edge Compatibility** (40% weight)

   - Compares edge regions of adjacent pieces
   - **Methods**: Histogram correlation, gradient magnitude
   - **Impact**: Pieces with matching edges score higher

2. **Color Consistency** (30% weight)

   - Color histogram comparison using Earth Mover's Distance
   - **Impact**: Ensures color continuity across boundaries
   - **Reference**: EMD for histogram comparison [Rubner et al., 2000]

3. **Texture Matching** (20% weight)

   - Local Binary Patterns (LBP) for texture analysis
   - **Impact**: Matches texture patterns across seams
   - **Reference**: LBP for texture classification [Ojala et al., 2002]

4. **Structural Similarity** (10% weight)
   - SSIM on overlapping regions
   - **Impact**: Ensures structural continuity
   - **Reference**: SSIM for perceptual similarity [Wang et al., 2004]

#### Evolution Process:

1. **Initialization**: Random valid permutations
2. **Selection**: Tournament selection (picks best from random subset)
3. **Crossover**: Order crossover (preserves partial arrangements)
4. **Mutation**: Swap mutation (random piece exchanges)
5. **Elitism**: Preserve top solutions

**Convergence**: Algorithm stops when:

- Maximum generations reached, OR
- No improvement for 20 consecutive generations (early stopping)

#### Similarity Metrics:

Multi-metric approach for robust piece matching:

1. **SSIM** (50% weight)

   - Structural Similarity Index
   - **Impact**: Perceptual similarity between pieces
   - **Reference**: [Wang et al., 2004]

2. **Color Histogram Correlation** (30% weight)

   - Compares color distributions
   - **Impact**: Matches overall color composition

3. **Mean Absolute Error** (20% weight)
   - Pixel-wise difference
   - **Impact**: Penalizes large pixel mismatches

#### Key Parameters:

- `--neighborhood N`: Maximum distance for partial credit (default: 1)
- `--partial-credit X`: Base credit for distance-1 neighbors (default: 0.6)
- `--similarity-threshold X`: Minimum similarity to count (default: 0.7)
- `--quiet`: Suppress per-piece output, show only final statistics

#### Output:

```
Puzzles checked:       110
Total pieces:          1760
Total exact matches:   1437 (91.6%)
Total partial matches: 125 (7.1%)
Relative positioning:  89 pieces with correct neighbors
Average accuracy:      94.86%
```

\*\*\*\*---

## Accuracy Checking

The `check_accuracy.py` script provides smart accuracy evaluation with partial credit for nearly-correct solutions:

### Features

- **Exact position matching**: Full credit (100%) for pieces in correct positions
- **Neighborhood matching**: Partial credit for pieces close to their correct position
- **Perceptual similarity**: Uses SSIM, histogram comparison, and MAE for robust matching
- **Configurable tolerance**: Adjust neighborhood size and partial credit factor

### Usage

Basic usage:

```bash
python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4
```

Advanced options:

```bash
# Increase neighborhood for more lenient scoring
python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4 --neighborhood 2

# Adjust partial credit factor (default: 0.6 for distance=1)
python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4 --partial-credit 0.5

# Check specific puzzle only
python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4 --puzzle-id 5

# Lower similarity threshold for more lenient matching
python scripts/check_accuracy.py -i data/puzzle_4x4 -o results/4x4 -g 4 --similarity-threshold 0.6
```

### How it Works

1. **Tile Splitting**: Divides original and solved images into NxN tiles
2. **Similarity Calculation**: Compares each original tile with all solved tiles using:
   - SSIM (50% weight) - structural similarity
   - Color histogram correlation (30% weight)
   - Mean Absolute Error (20% weight)
3. **Position Matching**: Finds best match for each tile
4. **Credit Calculation**:
   - Distance 0 (exact): 100% credit
   - Distance 1 (neighbor): 60% credit (default)
   - Distance 2: 30% credit
   - Distance N: `partial_credit / N`
5. **Overall Accuracy**: Sum of all credits / total pieces × 100%

### Output

The script provides:

- Per-piece match details (position, similarity, credit)
- Exact vs partial match counts
- Total accuracy percentage
- Overall statistics across multiple puzzles
- Best/worst performing puzzles

---

## Installation & Setup

The project is tested on Python 3.11 and 3.12 on Linux, Windows, and macOS.

### Prerequisites

```bash
pip install -r requirements.txt
```

---

## Advanced Usage

### Custom Parameters

#### Preprocessing

```bash
python3 scripts/preprocess_puzzles.py \
  -i data/puzzle_4x4 \
  -o output/custom \
  -g 4 \
  --num-images 50 \
  --start-id 10
```

#### Solving

```bash
python3 scripts/solve_from_preprocessed.py \
  -d output/4x4 \
  --puzzle-id 5 \
  --output-dir results \
  --method genetic \
  --generations 150 \
  --population 150
```

#### Accuracy

```bash
python3 scripts/check_accuracy.py \
  -i data/correct \
  -o final/4x4 \
  -g 4 \
  --neighborhood 2 \
  --partial-credit 0.7 \
  --similarity-threshold 0.65
```

---

## The Accuracy Checking Script

The `check_accuracy.py` script provides detailed evaluation capabilities:
