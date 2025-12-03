# Jigsaw Puzzle Solver

A jigsaw puzzle solver using _awesomeness_ and computer vision :)

## What it does

1. **Splits** puzzle images into NxN tiles (2x2, 4x4, 8x8)
2. **Upscales** low-resolution tiles using Lanczos + sharpening
3. **Preprocesses** tiles (grayscale, median blur)
4. **Segments** tiles (adaptive threshold, morphology)
5. **Extracts contours** (puzzle piece boundaries)
6. **Detects edges** (Canny edge detection)

## Usage

the project is tested on Python 3.11 and 3.12 on Arch Linux, Windows 11, and MacOS 26.

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Put your puzzle images in `data/puzzle_NxN/` folders (it's already there for you)

3. Open and run `phase1.ipynb` in Jupyter

4. you will find the processed tiles in `output/puzzle_NxN/` folders
