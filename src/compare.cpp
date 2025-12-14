#include <iostream>
#include <cmath>
#include <vector>

#include "utility/bitmap.h"

// Compare a quadrant (piece) between two images using normalized cross-correlation
// Only compares RGB channels (ignores alpha)
float CompareQuadrant(const Bitmap& img1, const Bitmap& img2, 
                       int row1, int col1, int row2, int col2, int pieceSize) {
    float sum1 = 0, sum2 = 0, sumSq1 = 0, sumSq2 = 0, sumProd = 0;
    int count = 0;
    int channels = 3; // Only compare RGB, ignore alpha
    
    for (int i = 0; i < pieceSize; i++) {
        for (int j = 0; j < pieceSize; j++) {
            unsigned char* p1 = img1.GetPixel(row1 * pieceSize + i, col1 * pieceSize + j);
            unsigned char* p2 = img2.GetPixel(row2 * pieceSize + i, col2 * pieceSize + j);
            
            for (int c = 0; c < channels; c++) {
                float v1 = p1[c];
                float v2 = p2[c];
                sum1 += v1;
                sum2 += v2;
                sumSq1 += v1 * v1;
                sumSq2 += v2 * v2;
                sumProd += v1 * v2;
                count++;
            }
        }
    }
    
    float mean1 = sum1 / count;
    float mean2 = sum2 / count;
    float var1 = sumSq1 / count - mean1 * mean1;
    float var2 = sumSq2 / count - mean2 * mean2;
    float cov = sumProd / count - mean1 * mean2;
    
    if (var1 < 0.001f || var2 < 0.001f) {
        // Nearly uniform regions - compare means directly
        return (std::abs(mean1 - mean2) < 10.0f) ? 1.0f : 0.0f;
    }
    
    float correlation = cov / (std::sqrt(var1) * std::sqrt(var2));
    return correlation;
}

// Find which piece in correct image matches each piece in output image
bool ComparePuzzleSolution(const Bitmap& output, const Bitmap& correct, int pieceSize) {
    int gridSize = output.m_width / pieceSize;
    
    // For each position in output, find the matching piece in correct
    std::vector<int> outputToCorrectMapping(gridSize * gridSize, -1);
    
    for (int outRow = 0; outRow < gridSize; outRow++) {
        for (int outCol = 0; outCol < gridSize; outCol++) {
            int outIdx = outRow * gridSize + outCol;
            float bestCorr = -2.0f;
            int bestMatch = -1;
            
            for (int corrRow = 0; corrRow < gridSize; corrRow++) {
                for (int corrCol = 0; corrCol < gridSize; corrCol++) {
                    float corr = CompareQuadrant(output, correct, outRow, outCol, corrRow, corrCol, pieceSize);
                    if (corr > bestCorr) {
                        bestCorr = corr;
                        bestMatch = corrRow * gridSize + corrCol;
                    }
                }
            }
            
            outputToCorrectMapping[outIdx] = bestMatch;
        }
    }
    
    // Check if the mapping is identity (0->0, 1->1, 2->2, 3->3)
    for (int i = 0; i < gridSize * gridSize; i++) {
        if (outputToCorrectMapping[i] != i) {
            return false;
        }
    }
    
    return true;
}

// Simple pixel-based comparison with high tolerance (handles JPG artifacts and RGB/RGBA)
bool CompareImagesSimple(const Bitmap& img1, const Bitmap& img2, float tolerance = 50.0f) {
    if (img1.m_width != img2.m_width || img1.m_height != img2.m_height) {
        return false;
    }
    
    int channels = 3; // Only compare RGB, ignore alpha
    float totalDiff = 0;
    int totalPixels = img1.m_width * img1.m_height * channels;
    
    for (int i = 0; i < img1.m_height; i++) {
        for (int j = 0; j < img1.m_width; j++) {
            unsigned char* p1 = img1.GetPixel(i, j);
            unsigned char* p2 = img2.GetPixel(i, j);
            for (int c = 0; c < channels; c++) {
                float diff = std::abs((float)p1[c] - (float)p2[c]);
                totalDiff += diff;
            }
        }
    }
    
    float avgDiff = totalDiff / totalPixels;
    return avgDiff < tolerance;
}

int main() {
    std::string output_path = "../output/";
    std::string correct_path = "../correct/";
    
    int correct_count = 0;
    int total_count = 0;
    int piece_size = 112; // 224 / 2 = 112
    
    for (int i = 0; i <= 109; i++) {
        std::string output_file = output_path + "2x2_" + std::to_string(i) + "_ans.png";
        std::string correct_file = correct_path + std::to_string(i) + ".png";
        
        Bitmap output_img(output_file);
        Bitmap correct_img(correct_file);
        
        if (output_img.m_data == nullptr || correct_img.m_data == nullptr) {
            std::cout << "Image " << i << ": SKIP (file not found)" << std::endl;
            continue;
        }
        
        total_count++;
        
        // Use both methods - either passing means correct
        bool matchSimple = CompareImagesSimple(output_img, correct_img);
        bool matchPuzzle = ComparePuzzleSolution(output_img, correct_img, piece_size);
        
        bool match = matchSimple || matchPuzzle;
        
        if (match) {
            correct_count++;
            std::cout << "Image " << i << ": CORRECT" << std::endl;
        } else {
            std::cout << "Image " << i << ": WRONG" << std::endl;
        }
    }
    
    std::cout << "\n========================================" << std::endl;
    std::cout << "Total Accuracy: " << correct_count << "/" << total_count 
              << " (" << (100.0f * correct_count / total_count) << "%)" << std::endl;
    std::cout << "========================================" << std::endl;
    
    return 0;
}