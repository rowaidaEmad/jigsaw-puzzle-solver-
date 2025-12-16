import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple, Set

EDGES = ["top", "right", "bottom", "left"]
OPPOSITE = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
ORIENTATION_IDX = {"top": 0, "bottom": 1, "left": 2, "right": 3}
INF_PENALTY = 1e6 
NON_BEST_MATCH_PENALTY = 5000.0 
LOOKAHEAD_WEIGHT = 0.001  # Small weight to lookahead score (must be much smaller than match score)

# --- Helper Functions (From previous iteration - kept for context) ---

def build_graph(pieces_dict: Dict[str, List], similarity) -> Dict[tuple, List[tuple]]:
    # ... (Function body remains the same)
    graph = defaultdict(list)
    pieces = pieces_dict.get("binary") or pieces_dict.get("original")
    if pieces is None:
        raise ValueError("pieces_dict must contain 'binary' or 'original' key")
    n = len(pieces)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            for e_i in EDGES:
                e_j = OPPOSITE[e_i]
                score = similarity.compute(i, j, ORIENTATION_IDX[e_i], pieces_dict)
                if isinstance(score, (list, np.ndarray)):
                    score = float(np.array(score).flatten()[0])
                graph[(i, e_i)].append((j, e_j, score))
                
    for key in graph:
        graph[key].sort(key=lambda x: x[2])
    return graph

def get_adjusted_score(piece_a: int, edge_a: str, piece_b: int, graph: Dict[tuple, List[tuple]]) -> float:
    # ... (Function body remains the same - applies NON_BEST_MATCH_PENALTY)
    candidates = graph.get((piece_a, edge_a))
    if not candidates:
        return INF_PENALTY

    raw_score = INF_PENALTY
    
    # Check the absolute best match
    best_match_piece = candidates[0][0]
    best_match_edge = candidates[0][1]
    
    # Search for the actual score of piece_b
    for neighbor_piece, neighbor_edge, score in candidates:
        if neighbor_piece == piece_b and neighbor_edge == OPPOSITE[edge_a]:
            raw_score = score
            break

    if raw_score == INF_PENALTY:
        return INF_PENALTY
        
    # Apply penalty if it's not the absolute best match for the neighbor
    if not (best_match_piece == piece_b and best_match_edge == OPPOSITE[edge_a]):
        return raw_score + NON_BEST_MATCH_PENALTY
    
    return raw_score

def is_piece_boundary_candidate(piece_idx: int, rows: int, cols: int, best_buddies: Dict[tuple, tuple]) -> Set[str]:
    # ... (Function body remains the same)
    boundary_edges = set()
    for edge in EDGES:
        if (piece_idx, edge) not in best_buddies:
            boundary_edges.add(edge)
            
    return boundary_edges

# --- Main Solver Function (Enhanced) ---

def solve_graph(pieces_dict: Dict[str, List], rows: int, cols: int, similarity) -> List[int]:
    """
    Graph-based greedy solver with Lookahead Heuristic, strict Best-Buddy checks, 
    and boundary awareness.
    """
    pieces = pieces_dict.get("original", [])
    n_pieces = len(pieces)
    used = set()
    grid = [[-1 for _ in range(cols)] for _ in range(rows)]
    
    graph = build_graph(pieces_dict, similarity)
    
    # Strict Best-Buddy Check: Only keep mutually verified matches (high confidence)
    best_buddies = {}
    for key, candidates in graph.items():
        if candidates:
            candidate = candidates[0] 
            reverse_candidates = graph.get((candidate[0], candidate[1]), [])
            if reverse_candidates and reverse_candidates[0][0] == key[0]:
                best_buddies[key] = candidate
                
    # --- Best-Fit Function (Crucially Modified) ---
    def best_fit(r, c):
        best_piece = None
        best_score = float('inf')
        
        required_boundary_edges = set()
        if r == 0: required_boundary_edges.add("top")
        if r == rows - 1: required_boundary_edges.add("bottom")
        if c == 0: required_boundary_edges.add("left")
        if c == cols - 1: required_boundary_edges.add("right")
            
        # Optimization: Pre-filter potential pieces (top 10 matches of neighbors)
        potential_pieces = range(n_pieces)
        if r > 0 or c > 0:
            candidate_indices = set(range(n_pieces))
            if r > 0:
                top_candidates = graph.get((grid[r-1][c], "bottom"), [])
                candidate_indices = candidate_indices.intersection({i for i, _, _ in top_candidates[:min(n_pieces, 10)]})
            if c > 0:
                left_candidates = graph.get((grid[r][c-1], "right"), [])
                candidate_indices = candidate_indices.intersection({i for i, _, _ in left_candidates[:min(n_pieces, 10)]})
            if candidate_indices:
                potential_pieces = candidate_indices

        for i in potential_pieces:
            if i in used:
                continue
            
            # --- 1. Boundary Heuristic Penalty ---
            boundary_penalty = 0
            piece_boundary_edges = is_piece_boundary_candidate(i, rows, cols, best_buddies)
            for edge in required_boundary_edges:
                if edge not in piece_boundary_edges:
                    boundary_penalty += INF_PENALTY / 10.0
            
            # --- 2. Compatibility Score Calculation (Top/Left) ---
            compatibility_score = 0
            if r > 0:
                compatibility_score += get_adjusted_score(grid[r-1][c], "bottom", i, graph)
            if c > 0:
                compatibility_score += get_adjusted_score(grid[r][c-1], "right", i, graph)

            # --- 3. Lookahead Penalty (NEW) ---
            lookahead_score = 0
            
            # Check potential fit for the RIGHT edge (if not a boundary)
            if c < cols - 1:
                # Add the raw score of the best match for the candidate's right edge
                right_candidates = graph.get((i, "right"), [])
                if right_candidates:
                    lookahead_score += right_candidates[0][2]
                else:
                    lookahead_score += NON_BEST_MATCH_PENALTY # Penalize pieces with no possible right match
                    
            # Check potential fit for the BOTTOM edge (if not a boundary)
            if r < rows - 1:
                # Add the raw score of the best match for the candidate's bottom edge
                bottom_candidates = graph.get((i, "bottom"), [])
                if bottom_candidates:
                    lookahead_score += bottom_candidates[0][2]
                else:
                    lookahead_score += NON_BEST_MATCH_PENALTY # Penalize pieces with no possible bottom match

            # --- 4. Final Score Tally ---
            # Lookahead score is weighted heavily to be a tie-breaker/contextual factor
            final_score = compatibility_score + boundary_penalty + (lookahead_score * LOOKAHEAD_WEIGHT)

            if final_score < best_score:
                best_score = final_score
                best_piece = i
            # Optional: Add a tie-breaker if scores are exactly equal (e.g., lower index i)

        return best_piece

    # --- Initial Piece Selection (Corner Bonus) ---
    # (No functional change here, relies on Best-Buddies and Corner Bonus)
    if rows > 0 and cols > 0:
        start_piece = 0
        min_total_best_score = float('inf')
        
        for i in range(n_pieces):
            total_best_score = 0
            boundary_edges_count = 0
            for edge in EDGES:
                match = best_buddies.get((i, edge))
                if match:
                    total_best_score += match[2]
                else:
                    total_best_score += INF_PENALTY / 10.0 
                    boundary_edges_count += 1
            
            # Strong bonus for being a corner piece (2 boundary edges)
            if boundary_edges_count == 2:
                total_best_score -= INF_PENALTY / 5.0 

            if total_best_score < min_total_best_score:
                min_total_best_score = total_best_score
                start_piece = i

        grid[0][0] = start_piece
        used.add(start_piece)
        
        # Fill remaining grid
        for r in range(rows):
            for c in range(cols):
                if r == 0 and c == 0:
                    continue 

                piece = best_fit(r, c)
                
                if piece is None:
                    try:
                        piece = next(i for i in range(n_pieces) if i not in used)
                    except StopIteration:
                        break 
                
                grid[r][c] = piece
                used.add(piece)

    # flatten grid
    solved_order = [grid[r][c] for r in range(rows) for c in range(cols)]
    return solved_order