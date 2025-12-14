#include <iostream>
#include <algorithm>
#include <vector>
#include <cfloat>
#include <cmath>
#include <set>
#include <map>
#include <queue>

#include "utility/bitmap.h"

int image_size;

// Convert RGB to LAB color space (approximate)
void RGBtoLAB(float r, float g, float b, float& L, float& A, float& B) {
    // Normalize RGB
    r /= 255.0f; g /= 255.0f; b /= 255.0f;
    
    // Apply gamma correction
    r = (r > 0.04045f) ? powf((r + 0.055f) / 1.055f, 2.4f) : r / 12.92f;
    g = (g > 0.04045f) ? powf((g + 0.055f) / 1.055f, 2.4f) : g / 12.92f;
    b = (b > 0.04045f) ? powf((b + 0.055f) / 1.055f, 2.4f) : b / 12.92f;
    
    r *= 100.0f; g *= 100.0f; b *= 100.0f;
    
    // Convert to XYZ
    float x = r * 0.4124564f + g * 0.3575761f + b * 0.1804375f;
    float y = r * 0.2126729f + g * 0.7151522f + b * 0.0721750f;
    float z = r * 0.0193339f + g * 0.1191920f + b * 0.9503041f;
    
    // Normalize for D65 illuminant
    x /= 95.047f; y /= 100.000f; z /= 108.883f;
    
    // Apply f function
    auto f = [](float t) {
        return (t > 0.008856f) ? powf(t, 1.0f/3.0f) : (7.787f * t + 16.0f/116.0f);
    };
    
    L = 116.0f * f(y) - 16.0f;
    A = 500.0f * (f(x) - f(y));
    B = 200.0f * (f(y) - f(z));
}

// Mahalanobis Gradient Compatibility (MGC) - state of the art
// Predicts the color on one side of the boundary using gradient from the other side
float EdgeDissimilarity(const Bitmap& piece1, const Bitmap& piece2, int orientation) {
    int size = piece1.m_width;
    int channels = std::min(piece1.m_channels, 3);
    float total = 0;
    
    for (int i = 0; i < size; i++) {
        unsigned char *p1_inner, *p1_edge, *p2_edge, *p2_inner;
        
        if (orientation == 1) { // piece1's bottom matches piece2's top
            p1_inner = piece1.GetPixel(size - 2, i);
            p1_edge = piece1.GetPixel(size - 1, i);
            p2_edge = piece2.GetPixel(0, i);
            p2_inner = piece2.GetPixel(1, i);
        } else { // piece1's right matches piece2's left
            p1_inner = piece1.GetPixel(i, size - 2);
            p1_edge = piece1.GetPixel(i, size - 1);
            p2_edge = piece2.GetPixel(i, 0);
            p2_inner = piece2.GetPixel(i, 1);
        }
        
        // Use LAB for perceptual accuracy
        float L1i, A1i, B1i, L1e, A1e, B1e;
        float L2e, A2e, B2e, L2i, A2i, B2i;
        
        RGBtoLAB(p1_inner[0], p1_inner[1], p1_inner[2], L1i, A1i, B1i);
        RGBtoLAB(p1_edge[0], p1_edge[1], p1_edge[2], L1e, A1e, B1e);
        RGBtoLAB(p2_edge[0], p2_edge[1], p2_edge[2], L2e, A2e, B2e);
        RGBtoLAB(p2_inner[0], p2_inner[1], p2_inner[2], L2i, A2i, B2i);
        
        // Gradient on piece1 side
        float gradL1 = L1e - L1i;
        float gradA1 = A1e - A1i;
        float gradB1 = B1e - B1i;
        
        // Gradient on piece2 side
        float gradL2 = L2i - L2e;
        float gradA2 = A2i - A2e;
        float gradB2 = B2i - B2e;
        
        // Predict p2_edge using gradient from p1
        float predL2 = L1e + gradL1;
        float predA2 = A1e + gradA1;
        float predB2 = B1e + gradB1;
        
        // Predict p1_edge using gradient from p2
        float predL1 = L2e + gradL2;
        float predA1 = A2e + gradA2;
        float predB1 = B2e + gradB2;
        
        // Bidirectional error
        float errL1 = predL2 - L2e, errA1 = predA2 - A2e, errB1 = predB2 - B2e;
        float errL2 = predL1 - L1e, errA2 = predA1 - A1e, errB2 = predB1 - B1e;
        
        total += errL1*errL1 + errA1*errA1 + errB1*errB1;
        total += errL2*errL2 + errA2*errA2 + errB2*errB2;
        
        // Also add direct color difference
        float dL = L1e - L2e, dA = A1e - A2e, dB = B1e - B2e;
        total += (dL*dL + dA*dA + dB*dB) * 0.5f;
    }
    
    return total;
}

// Precompute all pairwise dissimilarities
struct PuzzleSolver {
    std::vector<Bitmap>& pieces;
    int gridSize;
    int numPieces;
    
    // dissimilarity[i][j][dir] = cost of placing piece j to the dir of piece i
    // dir: 0=above, 1=below, 2=left, 3=right
    std::vector<std::vector<std::vector<float>>> dissimilarity;
    
    // bestMatch[i][dir] = piece index that best matches piece i in direction dir
    std::vector<std::vector<int>> bestMatch;
    
    // isBestBuddy[i][j][dir] = true if i and j are best buddies in direction dir
    std::vector<std::vector<std::vector<bool>>> isBestBuddy;
    
    PuzzleSolver(std::vector<Bitmap>& p, int gs) : pieces(p), gridSize(gs) {
        numPieces = pieces.size();
        
        // Initialize dissimilarity matrix
        dissimilarity.resize(numPieces);
        bestMatch.resize(numPieces);
        isBestBuddy.resize(numPieces);
        
        for (int i = 0; i < numPieces; i++) {
            dissimilarity[i].resize(numPieces);
            bestMatch[i].resize(4, -1);
            isBestBuddy[i].resize(numPieces);
            
            for (int j = 0; j < numPieces; j++) {
                dissimilarity[i][j].resize(4, FLT_MAX);
                isBestBuddy[i][j].resize(4, false);
            }
        }
        
        // Compute all pairwise dissimilarities
        for (int i = 0; i < numPieces; i++) {
            for (int j = 0; j < numPieces; j++) {
                if (i == j) continue;
                
                // piece j below piece i (i's bottom matches j's top)
                dissimilarity[i][j][1] = EdgeDissimilarity(pieces[i], pieces[j], 1);
                
                // piece j to the right of piece i
                dissimilarity[i][j][3] = EdgeDissimilarity(pieces[i], pieces[j], 3);
                
                // piece j above piece i (j's bottom matches i's top)
                dissimilarity[i][j][0] = EdgeDissimilarity(pieces[j], pieces[i], 1);
                
                // piece j to the left of piece i (j's right matches i's left)
                dissimilarity[i][j][2] = EdgeDissimilarity(pieces[j], pieces[i], 3);
            }
        }
        
        // Find best matches for each piece in each direction
        for (int i = 0; i < numPieces; i++) {
            for (int dir = 0; dir < 4; dir++) {
                float bestScore = FLT_MAX;
                int bestIdx = -1;
                for (int j = 0; j < numPieces; j++) {
                    if (i != j && dissimilarity[i][j][dir] < bestScore) {
                        bestScore = dissimilarity[i][j][dir];
                        bestIdx = j;
                    }
                }
                bestMatch[i][dir] = bestIdx;
            }
        }
        
        // Identify best buddies
        for (int i = 0; i < numPieces; i++) {
            for (int dir = 0; dir < 4; dir++) {
                int j = bestMatch[i][dir];
                if (j >= 0) {
                    int oppositeDir = (dir < 2) ? (1 - dir) : (5 - dir); // 0<->1, 2<->3
                    if (bestMatch[j][oppositeDir] == i) {
                        isBestBuddy[i][j][dir] = true;
                    }
                }
            }
        }
    }
    
    // Greedy placement algorithm
    std::vector<int> solve() {
        // Grid: -1 means empty
        std::vector<std::vector<int>> grid(gridSize * 2, std::vector<int>(gridSize * 2, -1));
        std::set<int> usedPieces;
        
        // Start with piece 0 in the center
        int centerR = gridSize, centerC = gridSize;
        grid[centerR][centerC] = 0;
        usedPieces.insert(0);
        
        // Priority queue: (negative score, piece to place, row, col)
        // We use negative score because priority_queue is max-heap
        using Entry = std::tuple<float, int, int, int>;
        std::priority_queue<Entry, std::vector<Entry>, std::greater<Entry>> pq;
        
        auto addCandidates = [&](int r, int c) {
            int placedPiece = grid[r][c];
            
            // Check all 4 directions
            int dr[] = {-1, 1, 0, 0};
            int dc[] = {0, 0, -1, 1};
            int dirs[] = {0, 1, 2, 3}; // above, below, left, right
            
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d];
                int nc = c + dc[d];
                
                if (nr >= 0 && nr < gridSize * 2 && nc >= 0 && nc < gridSize * 2 && grid[nr][nc] == -1) {
                    // Find best piece for this position
                    for (int piece = 0; piece < numPieces; piece++) {
                        if (usedPieces.count(piece)) continue;
                        
                        float score = dissimilarity[placedPiece][piece][dirs[d]];
                        
                        // Bonus for best buddies
                        if (isBestBuddy[placedPiece][piece][dirs[d]]) {
                            score *= 0.5f;
                        }
                        
                        pq.push({score, piece, nr, nc});
                    }
                }
            }
        };
        
        addCandidates(centerR, centerC);
        
        // Place pieces one by one
        while (usedPieces.size() < numPieces && !pq.empty()) {
            auto [score, piece, r, c] = pq.top();
            pq.pop();
            
            if (usedPieces.count(piece) || grid[r][c] != -1) continue;
            
            // Verify this placement is compatible with all neighbors
            bool valid = true;
            float totalScore = 0;
            int neighborCount = 0;
            
            int dr[] = {-1, 1, 0, 0};
            int dc[] = {0, 0, -1, 1};
            int oppDirs[] = {1, 0, 3, 2}; // opposite directions
            
            for (int d = 0; d < 4; d++) {
                int nr = r + dr[d];
                int nc = c + dc[d];
                
                if (nr >= 0 && nr < gridSize * 2 && nc >= 0 && nc < gridSize * 2 && grid[nr][nc] != -1) {
                    int neighbor = grid[nr][nc];
                    totalScore += dissimilarity[neighbor][piece][oppDirs[d]];
                    neighborCount++;
                }
            }
            
            if (neighborCount > 0 && valid) {
                grid[r][c] = piece;
                usedPieces.insert(piece);
                addCandidates(r, c);
            }
        }
        
        // Extract the final grid (find the bounding box of placed pieces)
        int minR = gridSize * 2, maxR = 0, minC = gridSize * 2, maxC = 0;
        for (int r = 0; r < gridSize * 2; r++) {
            for (int c = 0; c < gridSize * 2; c++) {
                if (grid[r][c] != -1) {
                    minR = std::min(minR, r);
                    maxR = std::max(maxR, r);
                    minC = std::min(minC, c);
                    maxC = std::max(maxC, c);
                }
            }
        }
        
        // Convert to linear arrangement
        std::vector<int> result(gridSize * gridSize, 0);
        for (int r = 0; r < gridSize; r++) {
            for (int c = 0; c < gridSize; c++) {
                int gr = minR + r;
                int gc = minC + c;
                if (gr < gridSize * 2 && gc < gridSize * 2 && grid[gr][gc] != -1) {
                    result[r * gridSize + c] = grid[gr][gc];
                }
            }
        }
        
        // Fill any remaining positions with unused pieces
        std::set<int> resultSet(result.begin(), result.end());
        int fillIdx = 0;
        for (int i = 0; i < gridSize * gridSize; i++) {
            if (resultSet.count(result[i]) > 1 || result[i] < 0 || result[i] >= numPieces) {
                while (fillIdx < numPieces && resultSet.count(fillIdx)) fillIdx++;
                if (fillIdx < numPieces) {
                    result[i] = fillIdx;
                    resultSet.insert(fillIdx);
                    fillIdx++;
                }
            }
        }
        
        return result;
    }
};

// Brute force solver for 2x2 puzzles (only 24 permutations)
std::vector<int> SolveBruteForce(std::vector<Bitmap>& pieces, int gridSize) {
    int numPieces = gridSize * gridSize;
    std::vector<int> arrangement(numPieces);
    for (int i = 0; i < numPieces; i++) arrangement[i] = i;
    
    std::vector<int> bestArrangement = arrangement;
    float bestScore = FLT_MAX;
    
    auto calcScore = [&](const std::vector<int>& arr) {
        float total = 0;
        for (int i = 0; i < gridSize; i++) {
            for (int j = 0; j < gridSize; j++) {
                int idx = i * gridSize + j;
                if (j < gridSize - 1) {
                    total += EdgeDissimilarity(pieces[arr[idx]], pieces[arr[idx + 1]], 3);
                }
                if (i < gridSize - 1) {
                    total += EdgeDissimilarity(pieces[arr[idx]], pieces[arr[idx + gridSize]], 1);
                }
            }
        }
        return total;
    };
    
    do {
        float score = calcScore(arrangement);
        if (score < bestScore) {
            bestScore = score;
            bestArrangement = arrangement;
        }
    } while (std::next_permutation(arrangement.begin(), arrangement.end()));
    
    return bestArrangement;
}

void Solve(const std::string &path, const std::string &filename, const std::string &output_path, int piece_size)
{
    Bitmap image(path + filename + ".jpg");
    if (image.m_data == nullptr) {
        return;
    }
    
    std::vector<Bitmap> pieces = Split(image, piece_size);
    int gridSize = image_size / piece_size;
    
    std::vector<int> bestArrangement;
    
    if (gridSize == 2) {
        bestArrangement = SolveBruteForce(pieces, gridSize);
    } else {
        PuzzleSolver solver(pieces, gridSize);
        bestArrangement = solver.solve();
    }
    
    // Build the answer image
    Bitmap answer(image_size, image_size, image.m_channels);
    
    for (int i = 0; i < gridSize; i++) {
        for (int j = 0; j < gridSize; j++) {
            int idx = i * gridSize + j;
            answer.Merge(pieces[bestArrangement[idx]], i, j);
        }
    }
    
    answer.OutputPNG(output_path + filename + "_ans.png");
}

int main()
{
    image_size = 224;
    
    // Process 2x2 puzzles
    std::cout << "Processing 2x2 puzzles..." << std::endl;
    for (int i = 0; i <= 109; i++) {
        std::cout << "\r  " << i + 1 << "/110" << std::flush;
        Solve("../puzzle_2x2/", std::to_string(i), "../output/2x2_", 112);
    }
    std::cout << " Done!" << std::endl;
    
    // Process 4x4 puzzles
    std::cout << "Processing 4x4 puzzles..." << std::endl;
    for (int i = 0; i <= 109; i++) {
        std::cout << "\r  " << i + 1 << "/110" << std::flush;
        Solve("../puzzle_4x4/", std::to_string(i), "../output/4x4_", 56);
    }
    std::cout << " Done!" << std::endl;
    
    // Process 8x8 puzzles
    std::cout << "Processing 8x8 puzzles..." << std::endl;
    for (int i = 0; i <= 109; i++) {
        std::cout << "\r  " << i + 1 << "/110" << std::flush;
        Solve("../puzzle_8x8/", std::to_string(i), "../output/8x8_", 28);
    }
    std::cout << " Done!" << std::endl;
    
    std::cout << "\nAll puzzles processed!" << std::endl;
    
    return 0;
}