#include <iostream>
#include <cmath>
#include <vector>
#include <iomanip>
#include <algorithm>

#include "utility/bitmap.h"

float EdgeSSD(const Bitmap& piece1, const Bitmap& piece2, int orientation) {
    int size = piece1.m_width;
    float total = 0;
    
    for (int i = 0; i < size; i++) {
        unsigned char *p1, *p2;
        
        if (orientation == 1) { // piece1's bottom matches piece2's top
            p1 = piece1.GetPixel(size - 1, i);
            p2 = piece2.GetPixel(0, i);
        } else { // piece1's right matches piece2's left  
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
    // Analyze image 1 in detail
    Bitmap puzzle("../puzzle_2x2/1.jpg");
    
    // Split into 4 pieces
    int pieceSize = 112;
    std::vector<Bitmap> pieces = Split(puzzle, pieceSize);
    
    std::cout << "=== Image 1 Analysis ===\n\n";
    
    // Print ALL edge dissimilarities
    std::cout << "Horizontal edges (piece i right -> piece j left):\n";
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            if (i == j) continue;
            float score = EdgeSSD(pieces[i], pieces[j], 3);
            std::cout << "  " << i << " -> " << j << ": " << std::fixed << std::setprecision(1) << score << "\n";
        }
    }
    
    std::cout << "\nVertical edges (piece i bottom -> piece j top):\n";
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            if (i == j) continue;
            float score = EdgeSSD(pieces[i], pieces[j], 1);
            std::cout << "  " << i << " -> " << j << ": " << std::fixed << std::setprecision(1) << score << "\n";
        }
    }
    
    // Brute force evaluate all permutations
    std::cout << "\n=== All 24 permutations scored ===\n";
    std::vector<int> arr = {0, 1, 2, 3};
    
    auto calcScore = [&](const std::vector<int>& a) {
        float total = 0;
        // Horizontal: 0-1, 2-3
        total += EdgeSSD(pieces[a[0]], pieces[a[1]], 3);
        total += EdgeSSD(pieces[a[2]], pieces[a[3]], 3);
        // Vertical: 0-2, 1-3
        total += EdgeSSD(pieces[a[0]], pieces[a[2]], 1);
        total += EdgeSSD(pieces[a[1]], pieces[a[3]], 1);
        return total;
    };
    
    std::vector<std::pair<float, std::vector<int>>> results;
    do {
        float score = calcScore(arr);
        results.push_back({score, arr});
    } while (std::next_permutation(arr.begin(), arr.end()));
    
    std::sort(results.begin(), results.end());
    
    std::cout << "Top 5 arrangements (best to worst):\n";
    for (int i = 0; i < 5 && i < results.size(); i++) {
        std::cout << "  Score " << std::fixed << std::setprecision(1) << results[i].first << ": [";
        for (int j = 0; j < 4; j++) {
            std::cout << results[i].second[j];
            if (j < 3) std::cout << ",";
        }
        std::cout << "]\n";
    }
    
    // Now check against correct image
    Bitmap correct("../correct/1.png");
    std::vector<Bitmap> correctPieces = Split(correct, pieceSize);
    
    std::cout << "\nMapping shuffled pieces to correct pieces:\n";
    for (int i = 0; i < 4; i++) {
        float bestScore = 1e9;
        int bestMatch = -1;
        for (int j = 0; j < 4; j++) {
            // Compare piece i from puzzle to piece j from correct
            float sum = 0;
            for (int y = 0; y < pieceSize; y++) {
                for (int x = 0; x < pieceSize; x++) {
                    unsigned char* p1 = pieces[i].GetPixel(y, x);
                    unsigned char* p2 = correctPieces[j].GetPixel(y, x);
                    for (int c = 0; c < 3; c++) {
                        float d = (float)p1[c] - (float)p2[c];
                        sum += d * d;
                    }
                }
            }
            if (sum < bestScore) {
                bestScore = sum;
                bestMatch = j;
            }
        }
        std::cout << "  Puzzle[" << i << "] = Correct[" << bestMatch << "]\n";
    }
    
    return 0;
}
