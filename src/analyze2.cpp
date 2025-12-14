#include <iostream>
#include <cmath>
#include <vector>
#include <iomanip>

#include "utility/bitmap.h"

float EdgeDissimilarity(const Bitmap& piece1, const Bitmap& piece2, int orientation) {
    int size = piece1.m_width;
    float total = 0;
    
    for (int i = 0; i < size; i++) {
        unsigned char *p1, *p2;
        
        if (orientation == 1) {
            p1 = piece1.GetPixel(size - 1, i);
            p2 = piece2.GetPixel(0, i);
        } else {
            p1 = piece1.GetPixel(i, size - 1);
            p2 = piece2.GetPixel(i, 0);
        }
        
        for (int c = 0; c < 3; c++) {
            float diff = (float)p1[c] - (float)p2[c];
            total += diff * diff;
        }
    }
    
    return total;
}

int main() {
    Bitmap puzzle("../puzzle_2x2/1.jpg");
    Bitmap correct("../correct/1.png");
    
    // Split into 4 pieces
    int pieceSize = 112;
    
    std::cout << "Analyzing Image 1\n\n";
    std::cout << "Correct arrangement dissimilarities:\n";
    
    // For a 2x2 puzzle, the correct arrangement means:
    // - Piece at (0,0) right edge matches piece at (0,1) left edge
    // - Piece at (0,0) bottom edge matches piece at (1,0) top edge  
    // - Piece at (1,0) right edge matches piece at (1,1) left edge
    // - Piece at (0,1) bottom edge matches piece at (1,1) top edge
    
    // Extract pieces from correct image
    struct Piece {
        unsigned char* data;
        int width, height, channels;
        unsigned char* GetPixel(int row, int col) const {
            return data + (row * width + col) * channels;
        }
    };
    
    // We'll analyze what the algorithm sees in the shuffled puzzle
    std::cout << "\nPuzzle piece (0,0) edges:\n";
    for (int i = 0; i < 5; i++) {
        unsigned char* p = puzzle.GetPixel(0, 112 - 1); // right edge, top pixel
        std::cout << "  Right edge pixel[" << i << "]: ";
        std::cout << (int)p[0] << "," << (int)p[1] << "," << (int)p[2] << "\n";
    }
    
    std::cout << "\nPuzzle piece (0,1) edges:\n";
    for (int i = 0; i < 5; i++) {
        unsigned char* p = puzzle.GetPixel(0 + i, 112); // left edge, from (0,112)
        std::cout << "  Left edge pixel[" << i << "]: ";
        std::cout << (int)p[0] << "," << (int)p[1] << "," << (int)p[2] << "\n";
    }
    
    return 0;
}
