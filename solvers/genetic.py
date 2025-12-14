"""
Genetic Algorithm Solver for Jigsaw Puzzles

Based on kernel-growing crossover with:
- Shared edges (from both parents)
- Best buddies (mutual best matches)
- Best available matches
"""

import random
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field

from utils.similarity import SimilarityCalculator


@dataclass
class Individual:
    """A candidate puzzle solution."""

    rows: int
    cols: int
    pieces: List[int]
    fitness: Optional[float] = field(default=None, repr=False)
    _idx: List[int] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._idx = [0] * len(self.pieces)
        for i, p in enumerate(self.pieces):
            self._idx[p] = i

    def get_neighbor(self, piece_id: int, orientation: int) -> int:
        """
        Get neighbor in given direction. Returns -1 if none.
        Orientation: 0=top, 1=bottom, 2=left, 3=right
        """
        idx = self._idx[piece_id]
        row, col = idx // self.cols, idx % self.cols

        if orientation == 0 and row > 0:
            return self.pieces[(row - 1) * self.cols + col]
        if orientation == 1 and row < self.rows - 1:
            return self.pieces[(row + 1) * self.cols + col]
        if orientation == 2 and col > 0:
            return self.pieces[row * self.cols + col - 1]
        if orientation == 3 and col < self.cols - 1:
            return self.pieces[row * self.cols + col + 1]
        return -1

    @staticmethod
    def random(rows: int, cols: int) -> "Individual":
        pieces = list(range(rows * cols))
        random.shuffle(pieces)
        return Individual(rows, cols, pieces)


class GeneticSolver:
    def __init__(
        self,
        pieces: List[np.ndarray],
        rows: int,
        columns: int,
        contours: Optional[List[np.ndarray]] = None,
        population_size: int = 100,
        elite_size: int = 4,
        generations: int = 100,
        similarity_calc: Optional[SimilarityCalculator] = None,
        tournament_k: int = 3,
        mutation_rate: float = 0.05,
        mutation_swaps: int = 1,
        local_iters: int = 10,
    ):
        self.pieces = pieces
        self.rows = rows
        self.cols = columns
        self.contours = contours
        self.n = rows * columns
        self.pop_size = population_size
        self.elite_size = elite_size
        self.generations = generations
        self.sim = similarity_calc or SimilarityCalculator()
        # New lightweight, high-impact params
        self.tournament_k = max(1, tournament_k)
        self.mutation_rate = float(mutation_rate)
        self.mutation_swaps = int(mutation_swaps)
        self.local_iters = int(local_iters)

        self.diss: Optional[np.ndarray] = None
        self.best_match: List[List[List[Tuple[float, int]]]] = []
        self.population: List[Individual] = []

    def _compute_dissimilarities(self):
        """Precompute all pairwise dissimilarities."""
        self.diss = np.zeros((self.n, self.n, 4))
        for i in range(self.n):
            c1 = self.contours[i] if self.contours else None
            for j in range(self.n):
                if i == j:
                    continue
                c2 = self.contours[j] if self.contours else None
                for k in range(4):
                    self.diss[i, j, k] = self.sim.compute(
                        self.pieces[i], self.pieces[j], k, c1, c2
                    )

    def _build_best_match_table(self):
        """Build sorted best-match lists for each piece/orientation."""
        assert self.diss is not None
        self.best_match = [[[] for _ in range(4)] for _ in range(self.n)]

        for i in range(self.n):
            for k in range(4):
                matches = [(self.diss[i, j, k], j) for j in range(self.n) if i != j]
                matches.sort()
                self.best_match[i][k] = matches

    def _fitness(self, ind: Individual) -> float:
        """Compute fitness (higher = better). Cached on individual."""
        if ind.fitness is not None:
            return ind.fitness

        assert self.diss is not None
        total = 1e-3

        # Horizontal adjacencies
        for r in range(self.rows):
            for c in range(self.cols - 1):
                idx = r * self.cols + c
                p1, p2 = ind.pieces[idx], ind.pieces[idx + 1]
                total += self.diss[p1, p2, 3]

        # Vertical adjacencies
        for r in range(self.rows - 1):
            for c in range(self.cols):
                idx = r * self.cols + c
                p1, p2 = ind.pieces[idx], ind.pieces[idx + self.cols]
                total += self.diss[p1, p2, 1]

        ind.fitness = 1000.0 / total
        return ind.fitness

    def _select_parents(self, count: int) -> List[Tuple[Individual, Individual]]:
        """Select parents. Use tournament selection if tournament_k > 1,
        otherwise fall back to fitness-proportional sampling."""
        parents = []
        if self.tournament_k > 1:
            k = min(self.tournament_k, len(self.population))

            def pick():
                candidates = random.sample(self.population, k)
                return max(candidates, key=self._fitness)

            for _ in range(count):
                parents.append((pick(), pick()))
            return parents

        # Fallback: roulette-wheel
        weights = [self._fitness(ind) for ind in self.population]
        total = sum(weights)
        probs = [w / total for w in weights]

        for _ in range(count):
            p1 = random.choices(self.population, weights=probs)[0]
            p2 = random.choices(self.population, weights=probs)[0]
            parents.append((p1, p2))
        return parents

    def _mutate(self, ind: Individual) -> Individual:
        """Simple swap mutation: perform `mutation_swaps` random swaps."""
        pieces = ind.pieces[:]
        for _ in range(self.mutation_swaps):
            a, b = random.sample(range(self.n), 2)
            pieces[a], pieces[b] = pieces[b], pieces[a]
        return Individual(self.rows, self.cols, pieces)

    def _local_optimize(self, ind: Individual, iters: int = None) -> Individual:
        """Lightweight hill-climb: try random swaps and keep improving ones."""
        if iters is None:
            iters = self.local_iters

        best = ind
        best_f = self._fitness(best)
        for _ in range(iters):
            a, b = random.sample(range(self.n), 2)
            new_pieces = best.pieces[:]
            new_pieces[a], new_pieces[b] = new_pieces[b], new_pieces[a]
            cand = Individual(self.rows, self.cols, new_pieces)
            f = self._fitness(cand)
            if f > best_f:
                best, best_f = cand, f
        return best

    def _crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        """Kernel-growing crossover."""
        kernel: Dict[int, Tuple[int, int]] = {}
        used_pos: set = set()
        bm_used = [[0] * 4 for _ in range(self.n)]

        min_r = max_r = min_c = max_c = 0

        def in_range(r: int, c: int) -> bool:
            rows = abs(min(min_r, r)) + abs(max(max_r, r))
            cols = abs(min(min_c, c)) + abs(max(max_c, c))
            return rows < self.rows and cols < self.cols

        delta = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        candidates: List[Tuple[float, int, int, int, Tuple[int, int]]] = []

        def add_candidate(piece: int, pos: Tuple[int, int], orient: int, orig: int):
            if piece < 0 or piece >= self.n:
                return

            # Shared edge: both parents agree
            n1 = parent1.get_neighbor(piece, orient)
            n2 = parent2.get_neighbor(piece, orient)
            if n1 == n2 and n1 >= 0 and n1 not in kernel:
                candidates.append((-100, orig, orient, n1, pos))
                return

            # Best buddy: mutual best match
            matches = self.best_match[piece][orient]
            if matches:
                buddy = matches[0][1]
                reverse = self.best_match[buddy][orient ^ 1]
                if reverse and reverse[0][1] == piece:
                    if (
                        parent1.get_neighbor(piece, orient) == buddy
                        or parent2.get_neighbor(piece, orient) == buddy
                    ):
                        if buddy not in kernel:
                            candidates.append((-10, orig, orient, buddy, pos))
                            return

            # Best available match
            idx = bm_used[piece][orient]
            while idx < len(matches):
                _, j = matches[idx]
                bm_used[piece][orient] = idx + 1
                if j not in kernel:
                    candidates.append((matches[idx][0], orig, orient, j, pos))
                    return
                idx += 1

        def add_kernel(piece: int, pos: Tuple[int, int]):
            nonlocal min_r, max_r, min_c, max_c
            kernel[piece] = pos
            used_pos.add(pos)
            min_r, max_r = min(min_r, pos[0]), max(max_r, pos[0])
            min_c, max_c = min(min_c, pos[1]), max(max_c, pos[1])

            for orient in range(4):
                dr, dc = delta[orient]
                new_pos = (pos[0] + dr, pos[1] + dc)
                if new_pos not in used_pos and in_range(new_pos[0], new_pos[1]):
                    add_candidate(piece, new_pos, orient, piece)

        # Start with random piece from parent1
        root = random.choice(parent1.pieces)
        add_kernel(root, (0, 0))

        iters = 0
        max_iters = self.n * 10

        while candidates and iters < max_iters:
            candidates.sort()
            _, orig, orient, piece, pos = candidates.pop(0)

            if pos in used_pos:
                continue
            if piece in kernel:
                add_candidate(orig, pos, orient, orig)
                continue

            add_kernel(piece, pos)
            iters += 1

        # Convert kernel to result
        result = [-1] * self.n
        for piece, (r, c) in kernel.items():
            idx = (r - min_r) * self.cols + (c - min_c)
            if 0 <= idx < self.n:
                result[idx] = piece

        # Fill gaps with unused pieces
        used = set(result)
        next_p = 0
        for i in range(len(result)):
            if result[i] == -1:
                while next_p in used:
                    next_p += 1
                result[i] = next_p
                used.add(next_p)
                next_p += 1

        return Individual(self.rows, self.cols, result)

    def solve(self) -> List[int]:
        """Run the genetic algorithm."""
        print("Computing dissimilarities...")
        self._compute_dissimilarities()
        self._build_best_match_table()

        print("Initializing population...")
        self.population = [
            Individual.random(self.rows, self.cols) for _ in range(self.pop_size)
        ]
        self.population.sort(key=self._fitness, reverse=True)

        best_score = 0.0
        stagnation = 0

        for gen in range(self.generations):
            elite = self.population[: self.elite_size]
            new_pop = list(elite)

            parents = self._select_parents(self.pop_size - self.elite_size)
            for p1, p2 in parents:
                child = self._crossover(p1, p2)
                # Mutation
                if random.random() < self.mutation_rate:
                    child = self._mutate(child)
                # Lightweight local improvement (keeps code small but effective)
                child = self._local_optimize(child)
                new_pop.append(child)

            self.population = new_pop
            self.population.sort(key=self._fitness, reverse=True)

            current = self._fitness(self.population[0])
            if current > best_score:
                best_score = current
                stagnation = 0
            else:
                stagnation += 1

            if gen % 10 == 0:
                print(f"Gen {gen}: fitness = {current:.4f}")

            if stagnation > 20:
                print(f"Early stop at gen {gen}")
                break

        best = max(self.population, key=self._fitness)
        print(f"Final fitness: {self._fitness(best):.4f}")
        return best.pieces
