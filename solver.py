import numpy as np
from itertools import permutations
from typing import List, Optional, Callable
import heapq

from dissimilarity import mgc_dissimilarity


class PuzzleSolver:
    def __init__(
        self,
        pieces: List[np.ndarray],
        grid_size: int,
        dissimilarity_fn: Optional[Callable] = None,
    ):
        self.pieces = pieces
        self.grid_size = grid_size
        self.num_pieces = len(pieces)
        self.dissimilarity_fn = dissimilarity_fn or mgc_dissimilarity

        self.diss_v = np.zeros((self.num_pieces, self.num_pieces))
        self.diss_h = np.zeros((self.num_pieces, self.num_pieces))
        self._compute_dissimilarities()

    def _compute_dissimilarities(self):
        for i in range(self.num_pieces):
            for j in range(self.num_pieces):
                if i != j:
                    self.diss_v[i, j] = self.dissimilarity_fn(
                        self.pieces[i], self.pieces[j], "vertical"
                    )
                    self.diss_h[i, j] = self.dissimilarity_fn(
                        self.pieces[i], self.pieces[j], "horizontal"
                    )

    def solve(self) -> List[int]:
        grid = np.full((self.grid_size, self.grid_size), -1, dtype=int)
        used = set()

        grid[0, 0] = 0
        used.add(0)

        pq = []

        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r, c] == -1:
                    continue

                placed = grid[r, c]

                if r + 1 < self.grid_size and grid[r + 1, c] == -1:
                    for p in range(self.num_pieces):
                        if p not in used:
                            score = self.diss_v[placed, p]
                            heapq.heappush(pq, (score, p, r + 1, c))

                if c + 1 < self.grid_size and grid[r, c + 1] == -1:
                    for p in range(self.num_pieces):
                        if p not in used:
                            score = self.diss_h[placed, p]
                            heapq.heappush(pq, (score, p, r, c + 1))

        while pq and len(used) < self.num_pieces:
            score, piece, r, c = heapq.heappop(pq)

            if piece in used or grid[r, c] != -1:
                continue

            grid[r, c] = piece
            used.add(piece)

            if r + 1 < self.grid_size and grid[r + 1, c] == -1:
                for p in range(self.num_pieces):
                    if p not in used:
                        heapq.heappush(pq, (self.diss_v[piece, p], p, r + 1, c))

            if c + 1 < self.grid_size and grid[r, c + 1] == -1:
                for p in range(self.num_pieces):
                    if p not in used:
                        heapq.heappush(pq, (self.diss_h[piece, p], p, r, c + 1))

        result = []
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if grid[r, c] != -1:
                    result.append(grid[r, c])
                else:
                    unused = [i for i in range(self.num_pieces) if i not in used]
                    result.append(unused[0] if unused else 0)
                    if unused:
                        used.add(unused[0])

        return result


def solve_brute_force(
    pieces: List[np.ndarray],
    grid_size: int,
    dissimilarity_fn: Optional[Callable] = None,
) -> List[int]:
    dissimilarity_fn = dissimilarity_fn or mgc_dissimilarity
    num_pieces = grid_size * grid_size

    def score(arr):
        total = 0.0
        for i in range(grid_size):
            for j in range(grid_size):
                idx = i * grid_size + j
                if j < grid_size - 1:
                    total += dissimilarity_fn(
                        pieces[arr[idx]], pieces[arr[idx + 1]], "horizontal"
                    )
                if i < grid_size - 1:
                    total += dissimilarity_fn(
                        pieces[arr[idx]], pieces[arr[idx + grid_size]], "vertical"
                    )
        return total

    best = min(permutations(range(num_pieces)), key=score)
    return list(best)


def solve_puzzle(
    pieces: List[np.ndarray], grid_size: int, method: str = "greedy"
) -> List[int]:
    if method == "brute_force":
        return solve_brute_force(pieces, grid_size)
    else:
        solver = PuzzleSolver(pieces, grid_size)
        return solver.solve()
