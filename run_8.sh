#!/bin/bash

# Jigsaw Puzzle Solver Pipeline - Quick and Dirty (8x8)
# Based on README commands

echo "=========================================="
echo "Jigsaw Puzzle Solver - 8x8 Pipeline"
echo "=========================================="

# Step 1: Preprocessing
echo ""
echo "Step 1: Preprocessing puzzles..."
echo "=========================================="
python3 scripts/preprocess_puzzles.py -i data/puzzle_8x8 -o output/8x8 -g 8

if [ $? -ne 0 ]; then
    echo "Error: Preprocessing failed!"
    exit 1
fi

# Step 2: Solving
echo ""
echo "Step 2: Solving puzzles..."
echo "=========================================="
python3 scripts/solve_from_preprocessed.py -d output/8x8 --all --output-dir final/8x8 --simple-names

if [ $? -ne 0 ]; then
    echo "Error: Solving failed!"
    exit 1
fi


# Step 3: Accuracy Check
echo ""
echo "Step 3: Checking accuracy..."
echo "=========================================="
python3 scripts/check_accuracy.py -i data/correct -o final/8x8 -g 8 --quiet

if [ $? -ne 0 ]; then
    echo "Error: Accuracy check failed!"
    exit 1
fi

echo ""
echo "=========================================="
echo "Pipeline completed successfully!"
echo "=========================================="
