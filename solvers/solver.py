"""
Puzzle Solver - Clean dispatcher for different solving methods.
"""

import numpy as np
from typing import List, Optional

from utils.similarity import SimilarityCalculator


def solve(
    pieces: List[np.ndarray],
    rows: int,
    cols: int,
    method: str = "genetic",
    contours: Optional[List[np.ndarray]] = None,
    similarity: Optional[SimilarityCalculator] = None,
    **kwargs,
) -> List[int]:
    """
    Solve a jigsaw puzzle.

    Args:
        pieces: List of piece images
        rows: Number of rows in the grid
        cols: Number of columns in the grid
        method: "greedy" or "genetic"
        contours: Optional contour images for each piece
        similarity: Custom similarity calculator
        **kwargs: Extra args for genetic (generations, population_size)

    Returns:
        List of piece indices in solved order
    """
    if method == "genetic":
        return _solve_genetic(pieces, rows, cols, contours, similarity, **kwargs)
    else:
        return _solve_greedy(pieces, rows, cols, contours, similarity)


def _solve_greedy(
    pieces: List[np.ndarray],
    rows: int,
    cols: int,
    contours: Optional[List[np.ndarray]] = None,
    similarity: Optional[SimilarityCalculator] = None,
) -> List[int]:
    """Greedy solver - places pieces one by one based on best local match."""
    import heapq

    sim = similarity or SimilarityCalculator()
    n = len(pieces)

    # Precompute dissimilarities
    diss_h = np.zeros((n, n))  # horizontal (left-right)
    diss_v = np.zeros((n, n))  # vertical (top-bottom)

    for i in range(n):
        c1 = contours[i] if contours else None
        for j in range(n):
            if i != j:
                c2 = contours[j] if contours else None
                diss_h[i, j] = sim.compute(pieces[i], pieces[j], 3, c1, c2)
                diss_v[i, j] = sim.compute(pieces[i], pieces[j], 1, c1, c2)

    # Greedy placement
    grid = np.full((rows, cols), -1, dtype=int)
    used = set()
    pq = []

    # Start with piece 0 at (0,0)
    grid[0, 0] = 0
    used.add(0)

    # Add candidates for neighbors of (0,0)
    def add_neighbors(r, c, placed):
        if r + 1 < rows and grid[r + 1, c] == -1:
            for p in range(n):
                if p not in used:
                    heapq.heappush(pq, (diss_v[placed, p], p, r + 1, c))
        if c + 1 < cols and grid[r, c + 1] == -1:
            for p in range(n):
                if p not in used:
                    heapq.heappush(pq, (diss_h[placed, p], p, r, c + 1))

    add_neighbors(0, 0, 0)

    while pq and len(used) < n:
        _, piece, r, c = heapq.heappop(pq)
        if piece in used or grid[r, c] != -1:
            continue

        grid[r, c] = piece
        used.add(piece)
        add_neighbors(r, c, piece)

    # Fill any remaining gaps
    result = []
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] != -1:
                result.append(grid[r, c])
            else:
                unused = [i for i in range(n) if i not in used]
                if unused:
                    result.append(unused[0])
                    used.add(unused[0])
                else:
                    result.append(0)

    return result


def _solve_genetic(
    pieces: List[np.ndarray],
    rows: int,
    cols: int,
    contours: Optional[List[np.ndarray]] = None,
    similarity: Optional[SimilarityCalculator] = None,
    **kwargs,
) -> List[int]:
    """Genetic algorithm solver."""
    from solvers.genetic import GeneticSolver

    solver = GeneticSolver(
        pieces=pieces,
        rows=rows,
        columns=cols,
        contours=contours,
        similarity_calc=similarity,
        population_size=kwargs.get("population_size", 100),
        generations=kwargs.get("generations", 100),
        tournament_k=kwargs.get("tournament_k", 3),
        mutation_rate=kwargs.get("mutation_rate", 0.05),
        mutation_swaps=kwargs.get("mutation_swaps", 1),
        local_iters=kwargs.get("local_iters", 10),
    )
    return solver.solve()
