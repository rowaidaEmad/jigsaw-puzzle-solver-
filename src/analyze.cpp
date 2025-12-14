#include <iostream>
#include <cmath>
#include <vector>

#include "utility/bitmap.h"

// Calculate mean color of a piece region
void getMeanColor(const Bitmap& img, int row, int col, int pieceSize, float* mean) {
    mean[0] = mean[1] = mean[2] = 0;
    int count = pieceSize * pieceSize;
    
    for (int i = 0; i < pieceSize; i++) {
        for (int j = 0; j < pieceSize; j++) {
            unsigned char* p = img.GetPixel(row * pieceSize + i, col * pieceSize + j);
            mean[0] += p[0];
            mean[1] += p[1];
            mean[2] += p[2];
        }
    }
    
    mean[0] /= count;
    mean[1] /= count;
    mean[2] /= count;
}

// Compare pieces using mean color
float comparePieces(const Bitmap& img1, int r1, int c1, const Bitmap& img2, int r2, int c2, int pieceSize) {
    float mean1[3], mean2[3];
    getMeanColor(img1, r1, c1, pieceSize, mean1);
    getMeanColor(img2, r2, c2, pieceSize, mean2);
    
    float diff = 0;
    for (int i = 0; i < 3; i++) {
        float d = mean1[i] - mean2[i];
        diff += d * d;
    }
    return std::sqrt(diff);
}

int main() {
    std::string puzzle_path = "../puzzle_2x2/";
    std::string correct_path = "../correct/";
    std::string output_path = "../output/";
    
    int pieceSize = 112;
    
    // Analyze a few failing images
    std::vector<int> failing = {1, 3, 4, 5, 6};
    
    for (int idx : failing) {
        Bitmap puzzle(puzzle_path + std::to_string(idx) + ".jpg");
        Bitmap correct(correct_path + std::to_string(idx) + ".png");
        Bitmap output(output_path + "2x2_" + std::to_string(idx) + "_ans.png");
        
        if (puzzle.m_data == nullptr || correct.m_data == nullptr || output.m_data == nullptr) {
            std::cout << "Image " << idx << ": SKIP (file not found)" << std::endl;
            continue;
        }
        
        std::cout << "\n=== Image " << idx << " ===" << std::endl;
        std::cout << "Puzzle pieces → Correct positions:" << std::endl;
        
        // For each piece in puzzle, find its position in correct
        for (int pr = 0; pr < 2; pr++) {
            for (int pc = 0; pc < 2; pc++) {
                float bestDiff = 1e9;
                int bestR = -1, bestC = -1;
                
                for (int cr = 0; cr < 2; cr++) {
                    for (int cc = 0; cc < 2; cc++) {
                        float diff = comparePieces(puzzle, pr, pc, correct, cr, cc, pieceSize);
                        if (diff < bestDiff) {
                            bestDiff = diff;
                            bestR = cr;
                            bestC = cc;
                        }
                    }
                }
                
                int puzzlePos = pr * 2 + pc;
                int correctPos = bestR * 2 + bestC;
                std::cout << "  Puzzle[" << puzzlePos << "] matches Correct[" << correctPos << "] (diff=" << bestDiff << ")" << std::endl;
            }
        }
        
        // Check output mapping
        std::cout << "Output pieces → Correct positions:" << std::endl;
        for (int or_ = 0; or_ < 2; or_++) {
            for (int oc = 0; oc < 2; oc++) {
                float bestDiff = 1e9;
                int bestR = -1, bestC = -1;
                
                for (int cr = 0; cr < 2; cr++) {
                    for (int cc = 0; cc < 2; cc++) {
                        float diff = comparePieces(output, or_, oc, correct, cr, cc, pieceSize);
                        if (diff < bestDiff) {
                            bestDiff = diff;
                            bestR = cr;
                            bestC = cc;
                        }
                    }
                }
                
                int outputPos = or_ * 2 + oc;
                int correctPos = bestR * 2 + bestC;
                bool isCorrect = (outputPos == correctPos);
                std::cout << "  Output[" << outputPos << "] matches Correct[" << correctPos << "] " 
                          << (isCorrect ? "✓" : "✗") << " (diff=" << bestDiff << ")" << std::endl;
            }
        }
    }
    
    return 0;
}
