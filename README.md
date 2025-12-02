# Jigsaw Puzzle Solver

what do we need to achieve??
we need to solve the puzzle...

how to `programatically`??

1. hold the image get
2. the pieces out of it
3. for each piece => do some sort of dynamic filtering to make dealing with the piece more ez in next steps
4. for all pieces with each other: try to do some sort of fitting with a score for every two pieces
5. sort them depending on this array and yaah get the final correct image

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Process all puzzles with greedy method (default)
python main.py

# Process only 2x2 puzzles
python main.py --only 2x2

# Use brute force method (only for small puzzles)
python main.py --only 2x2 --method brute_force

# Evaluate accuracy (requires data/correct/ folder)
python main.py --evaluate

# Process specific number of images
python main.py --num-images 50

# Combine options
python main.py --only 2x2 --method greedy --evaluate --num-images 10
```

**Options:**

- `--base-dir`: Input directory (default: `data`)
- `--output-dir`: Output directory (default: `output`)
- `--image-size`: Puzzle image size (default: 224)
- `--num-images`: Number of images to process (default: 110)
- `--only`: Process specific size: `2x2`, `4x4`, `8x8`, or `all` (default: `all`)
- `--method`: Solving method: `greedy` or `brute_force` (default: `greedy`)
- `--evaluate`: Evaluate accuracy after solving

**Note:** By default, the solver looks for puzzle images in the `data/` folder and saves results to `output/`. Make sure your puzzle images are placed in:

- `data/puzzle_2x2/` for 2x2 puzzles
- `data/puzzle_4x4/` for 4x4 puzzles
- `data/puzzle_8x8/` for 8x8 puzzles
