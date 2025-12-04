# Jigsaw Puzzle Solver

A jigsaw puzzle solver using _awesomeness_ and computer vision :)
we're live on: [puzzle-crisis.diran.app](https://puzzle-crisis.diran.app)

## What it does

For each input puzzle image (2×2, 4×4, or 8×8 grid), Phase 1:

1. **Splits** the puzzle into `N×N` rectangular tiles (pieces).
2. **Upscales** small/low-resolution tiles using **Lanczos interpolation** followed by light sharpening, to make edges clearer.
3. **Preprocesses** each tile:
   - convert to **grayscale**
   - apply **median blur** for noise reduction while preserving edges.
4. **Segments** each tile into foreground puzzle piece vs background using:
   - **adaptive thresholding**, then
   - **morphological operations** (opening/closing) to clean the mask.
5. **Extracts piece contours** from the cleaned mask.
6. **Detects edges** using **Canny edge detection** on the preprocessed tile, to be used later for edge-based matching.

The output of Phase 1 is:

- preprocessed tiles,
- binary masks for each piece,
- contours and edge maps that will be consumed in later phases (feature extraction and matching).

## Installation & Environment

the project is tested on Python 3.11 and 3.12 on Arch Linux, Windows 11, and MacOS 26.

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Put your puzzle images in `data/puzzle_NxN/` folders (it's already there for you)

3. Open and run `phase1.ipynb` in Jupyter

4. you will find the processed tiles in `output/puzzle_NxN/` folders
