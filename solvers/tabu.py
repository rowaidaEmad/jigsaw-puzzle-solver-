"""
Tabu Search Solver for grid-based tile jigsaw puzzles.

- Uses the SAME preprocessing + SimilarityCalculator as the rest of the project.
- Optimizes a global cost = sum of edge dissimilarities between adjacent tiles.
- Starts from an initial arrangement (greedy by default), then refines using Tabu Search.

Cost uses:
  horizontal adjacencies: sim.compute(p_left, p_right, 3, pieces_dict)
  vertical adjacencies:   sim.compute(p_top,  p_bottom, 1, pieces_dict)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import random
import numpy as np

from utils.similarity import SimilarityCalculator


@dataclass
class TabuParams:
    iterations: int = 3000
    tabu_tenure: int = 50
    neighborhood: int = 200  # how many random swap candidates to evaluate per iteration
    seed: Optional[int] = None


class TabuSolver:
    def __init__(
        self,
        pieces_dict: dict,
        rows: int,
        cols: int,
        similarity_calc: Optional[SimilarityCalculator] = None,
        initial: Optional[List[int]] = None,
        params: Optional[TabuParams] = None,
    ):
        self.pieces_dict = pieces_dict
        self.rows = rows
        self.cols = cols
        self.n = rows * cols
        self.sim = similarity_calc or SimilarityCalculator()
        self.params = params or TabuParams()

        if self.params.seed is not None:
            random.seed(self.params.seed)
            np.random.seed(self.params.seed)

        if initial is None:
            # fallback random init if not provided
            initial = list(range(self.n))
            random.shuffle(initial)

        if len(initial) != self.n:
            raise ValueError(f"Initial arrangement length {len(initial)} != {self.n}")

        self.arr = np.array(initial, dtype=int)

        # Precompute pairwise dissimilarities needed for cost:
        # diss_h[a,b] is cost of placing b to the RIGHT of a (orientation 3)
        # diss_v[a,b] is cost of placing b BELOW a (orientation 1)
        self.diss_h = np.zeros((self.n, self.n), dtype=np.float32)
        self.diss_v = np.zeros((self.n, self.n), dtype=np.float32)
        self._precompute_dissimilarities()

    def _precompute_dissimilarities(self) -> None:
        for i in range(self.n):
            for j in range(self.n):
                if i == j:
                    continue
                self.diss_h[i, j] = self.sim.compute(i, j, 3, self.pieces_dict)
                self.diss_v[i, j] = self.sim.compute(i, j, 1, self.pieces_dict)

    def _total_cost(self, arr: np.ndarray) -> float:
        """Sum of all adjacent mismatches (lower is better)."""
        cost = 0.0
        # Horizontal
        for r in range(self.rows):
            base = r * self.cols
            for c in range(self.cols - 1):
                a = arr[base + c]
                b = arr[base + c + 1]
                cost += float(self.diss_h[a, b])
        # Vertical
        for r in range(self.rows - 1):
            base = r * self.cols
            below = (r + 1) * self.cols
            for c in range(self.cols):
                a = arr[base + c]
                b = arr[below + c]
                cost += float(self.diss_v[a, b])
        return cost

    def _neighbors_of_index(self, idx: int) -> List[Tuple[int, str]]:
        """Return neighbor indices and type ('h' or 'v') for edges touching idx."""
        r, c = divmod(idx, self.cols)
        out = []

        # left edge: (left -> idx) horizontal
        if c > 0:
            out.append((idx - 1, "h"))  # edge between idx-1 and idx
        # right edge: (idx -> right) horizontal
        if c < self.cols - 1:
            out.append((idx, "h"))      # edge between idx and idx+1

        # up edge: (up -> idx) vertical
        if r > 0:
            out.append((idx - self.cols, "v"))  # edge between idx-cols and idx
        # down edge: (idx -> down) vertical
        if r < self.rows - 1:
            out.append((idx, "v"))              # edge between idx and idx+cols

        return out

    def _edge_cost_at(self, arr: np.ndarray, base_idx: int, kind: str) -> float:
        """
        Cost of an edge at a given base index.
        kind='h': compares arr[base_idx] with arr[base_idx+1]
        kind='v': compares arr[base_idx] with arr[base_idx+cols]
        """
        if kind == "h":
            a = arr[base_idx]
            b = arr[base_idx + 1]
            return float(self.diss_h[a, b])
        else:
            a = arr[base_idx]
            b = arr[base_idx + self.cols]
            return float(self.diss_v[a, b])

    def _delta_cost_swap(self, arr: np.ndarray, i: int, j: int) -> float:
        """
        Compute cost change if we swap positions i and j.
        Only recompute edges affected by i or j (<= ~12 edges).
        Returns: new_cost - old_cost (delta)
        """
        if i == j:
            return 0.0

        affected = set()
        for base, kind in self._neighbors_of_index(i):
            affected.add((base, kind))
        for base, kind in self._neighbors_of_index(j):
            affected.add((base, kind))

        old_sum = 0.0
        for base, kind in affected:
            old_sum += self._edge_cost_at(arr, base, kind)

        # swap in a copy (cheap because we only need local edges)
        tmp = arr.copy()
        tmp[i], tmp[j] = tmp[j], tmp[i]

        new_sum = 0.0
        for base, kind in affected:
            new_sum += self._edge_cost_at(tmp, base, kind)

        return new_sum - old_sum

    def solve(self) -> List[int]:
        params = self.params

        current = self.arr.copy()
        current_cost = self._total_cost(current)

        best = current.copy()
        best_cost = current_cost

        # tabu list: move -> expiration iteration
        # move is pair of indices (min_i, max_j)
        tabu: Dict[Tuple[int, int], int] = {}

        indices = list(range(self.n))

        for it in range(params.iterations):
            best_move = None
            best_move_delta = float("inf")
            best_move_new_cost = float("inf")

            # sample swap candidates
            for _ in range(params.neighborhood):
                i, j = random.sample(indices, 2)
                a, b = (i, j) if i < j else (j, i)
                move = (a, b)

                delta = self._delta_cost_swap(current, a, b)
                new_cost = current_cost + delta

                is_tabu = (move in tabu) and (tabu[move] > it)
                aspiration = new_cost < best_cost  # allow tabu if it beats global best

                if is_tabu and not aspiration:
                    continue

                if new_cost < best_move_new_cost:
                    best_move = move
                    best_move_delta = delta
                    best_move_new_cost = new_cost

            # If we found no admissible move, relax: pick a random move (rare)
            if best_move is None:
                a, b = sorted(random.sample(indices, 2))
                best_move = (a, b)
                best_move_delta = self._delta_cost_swap(current, a, b)
                best_move_new_cost = current_cost + best_move_delta

            # apply move
            a, b = best_move
            current[a], current[b] = current[b], current[a]
            current_cost = best_move_new_cost

            # mark tabu
            tabu[(a, b)] = it + params.tabu_tenure

            # update best
            if current_cost < best_cost:
                best = current.copy()
                best_cost = current_cost

        return best.tolist()
