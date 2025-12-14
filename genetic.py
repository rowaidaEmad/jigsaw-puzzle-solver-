import numpy as np
import random
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field

from similarity import SimilarityCalculator


@dataclass
class Individual:
    rows: int
    columns: int
    pieces: List[int]
    _fitness: Optional[float] = field(default=None, repr=False)
    _idx: List[int] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._idx = [0] * len(self.pieces)
        for i, p in enumerate(self.pieces):
            self._idx[p] = i

    def get_index(self, piece_id: int) -> int:
        return self._idx[piece_id]

    def get_neighbor(self, piece_id: int, orientation: int) -> int:
        """
        Get neighbor piece in given orientation.
        orientation: 0=top, 1=bottom, 2=left, 3=right
        Returns -1 if no neighbor.
        """
        idx = self._idx[piece_id]
        row, col = idx // self.columns, idx % self.columns

        if orientation == 0 and row > 0:
            return self.pieces[(row - 1) * self.columns + col]
        elif orientation == 1 and row < self.rows - 1:
            return self.pieces[(row + 1) * self.columns + col]
        elif orientation == 2 and col > 0:
            return self.pieces[row * self.columns + col - 1]
        elif orientation == 3 and col < self.columns - 1:
            return self.pieces[row * self.columns + col + 1]
        return -1

    @staticmethod
    def random(rows: int, columns: int) -> "Individual":
        pieces = list(range(rows * columns))
        random.shuffle(pieces)
        return Individual(rows, columns, pieces)


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
        similarity_calc: Optional[SimilarityCalculator] = None
    ):
        self.pieces = pieces
        self.rows = rows
        self.columns = columns
        self.contours = contours
        self.num_pieces = rows * columns
        self.population_size = population_size
        self.elite_size = elite_size
        self.generations = generations
        self.similarity = similarity_calc or SimilarityCalculator()

        self.dissimilarity_matrix: Optional[np.ndarray] = None
        self.best_match_table: List[List[List[Tuple[float, int]]]] = []
        self.population: List[Individual] = []
        self.fittest: Optional[Individual] = None

    def _compute_dissimilarities(self):
        n = self.num_pieces
        self.dissimilarity_matrix = np.zeros((n, n, 4))

        for i in range(n):
            c1 = self.contours[i] if self.contours else None
            for j in range(n):
                if i == j:
                    continue
                c2 = self.contours[j] if self.contours else None
                for k in range(4):
                    self.dissimilarity_matrix[i, j, k] = self.similarity.compute(
                        self.pieces[i], self.pieces[j], k, c1, c2
                    )

    def _build_best_match_table(self):
        n = self.num_pieces
        self.best_match_table = [[[] for _ in range(4)] for _ in range(n)]

        for i in range(n):
            for k in range(4):
                matches = []
                for j in range(n):
                    if i != j:
                        matches.append((self.dissimilarity_matrix[i, j, k], j))
                matches.sort()
                self.best_match_table[i][k] = matches

    def _fitness(self, ind: Individual) -> float:
        if ind._fitness is not None:
            return float(ind._fitness)

        total = 1e-3
        for i in range(self.rows):
            for j in range(self.columns - 1):
                idx = i * self.columns + j
                p1, p2 = ind.pieces[idx], ind.pieces[idx + 1]
                total += self.dissimilarity_matrix[p1, p2, 3]

        for i in range(self.rows - 1):
            for j in range(self.columns):
                idx = i * self.columns + j
                p1, p2 = ind.pieces[idx], ind.pieces[idx + self.columns]
                total += self.dissimilarity_matrix[p1, p2, 1]

        ind._fitness = 1000.0 / total
        return float(ind._fitness)

    def _select_parents(self, count: int) -> List[Tuple[Individual, Individual]]:
        weights = [self._fitness(ind) for ind in self.population]
        total_weight = sum(weights)
        probs = [w / total_weight for w in weights]

        parents = []
        for _ in range(count):
            p1 = random.choices(self.population, weights=probs)[0]
            p2 = random.choices(self.population, weights=probs)[0]
            parents.append((p1, p2))
        return parents

    def _crossover(self, parent1: Individual, parent2: Individual) -> Individual:
        kernel: Dict[int, Tuple[int, int]] = {}
        used_positions: set = set()
        best_match_used = [[0] * 4 for _ in range(self.num_pieces)]

        min_row = max_row = min_col = max_col = 0

        def is_in_range(row: int, col: int) -> bool:
            curr_rows = abs(min(min_row, row)) + abs(max(max_row, row))
            curr_cols = abs(min(min_col, col)) + abs(max(max_col, col))
            return curr_rows < self.rows and curr_cols < self.columns

        delta = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        candidates = []

        def add_candidate(piece_id: int, pos: Tuple[int, int], orientation: int, orig_piece: int):
            if piece_id < 0 or piece_id >= self.num_pieces:
                return

            n1 = parent1.get_neighbor(piece_id, orientation)
            n2 = parent2.get_neighbor(piece_id, orientation)
            if n1 == n2 and n1 not in kernel:
                candidates.append((-100, orig_piece, orientation, n1, pos))
                return

            matches = self.best_match_table[piece_id][orientation]
            if matches:
                first_buddy = matches[0][1]
                reverse_matches = self.best_match_table[first_buddy][orientation ^ 1]
                if reverse_matches and reverse_matches[0][1] == piece_id:
                    if parent1.get_neighbor(piece_id, orientation) == first_buddy or \
                       parent2.get_neighbor(piece_id, orientation) == first_buddy:
                        candidates.append((-10, orig_piece, orientation, first_buddy, pos))
                        return

            idx = best_match_used[piece_id][orientation]
            while idx < len(matches):
                p, j = matches[idx]
                best_match_used[piece_id][orientation] = idx + 1
                if j not in kernel:
                    candidates.append((p, orig_piece, orientation, j, pos))
                    return
                idx += 1

        def add_kernel(piece_id: int, pos: Tuple[int, int]):
            nonlocal min_row, max_row, min_col, max_col
            kernel[piece_id] = pos
            used_positions.add(pos)
            min_row = min(min_row, pos[0])
            max_row = max(max_row, pos[0])
            min_col = min(min_col, pos[1])
            max_col = max(max_col, pos[1])

            for orientation in range(4):
                dr, dc = delta[orientation]
                new_pos = (pos[0] + dr, pos[1] + dc)
                if new_pos not in used_positions and is_in_range(new_pos[0], new_pos[1]):
                    add_candidate(piece_id, new_pos, orientation, piece_id)

        root = random.choice(parent1.pieces)
        add_kernel(root, (0, 0))

        iterations = 0
        max_iterations = self.num_pieces * 10

        while candidates and iterations < max_iterations:
            candidates.sort()
            best = candidates.pop(0)
            _, orig_piece, orientation, piece_id, pos = best

            if pos in used_positions:
                continue
            if piece_id in kernel:
                add_candidate(orig_piece, pos, orientation, orig_piece)
                continue

            add_kernel(piece_id, pos)
            iterations += 1

        result = [-1] * self.num_pieces
        for piece_id, (row, col) in kernel.items():
            idx = (row - min_row) * self.columns + (col - min_col)
            if 0 <= idx < self.num_pieces:
                result[idx] = piece_id

        used = set(result)
        next_piece = 0
        for i in range(len(result)):
            if result[i] == -1:
                while next_piece in used:
                    next_piece += 1
                result[i] = next_piece
                used.add(next_piece)
                next_piece += 1

        return Individual(self.rows, self.columns, result)

    def solve(self) -> List[int]:
        print("Computing dissimilarities...")
        self._compute_dissimilarities()
        self._build_best_match_table()

        print("Initializing population...")
        self.population = [Individual.random(self.rows, self.columns) for _ in range(self.population_size)]
        self.population.sort(key=lambda x: self._fitness(x), reverse=True)

        best_score = 0
        stagnation = 0

        for gen in range(self.generations):
            elite = self.population[-self.elite_size:]
            self.fittest = elite[-1]

            new_pop = list(elite)
            parents = self._select_parents(self.population_size - self.elite_size)

            for p1, p2 in parents:
                child = self._crossover(p1, p2)
                new_pop.append(child)

            self.population = new_pop
            self.population.sort(key=lambda x: self._fitness(x))

            current_score = self._fitness(self.fittest)
            if current_score > best_score:
                best_score = current_score
                stagnation = 0
            else:
                stagnation += 1

            if gen % 10 == 0:
                print(f"Generation {gen}: fitness = {current_score:.4f}")

            if stagnation > 20:
                print(f"Early stopping at generation {gen}")
                break

        self.fittest = max(self.population, key=lambda x: self._fitness(x))
        print(f"Final fitness: {self._fitness(self.fittest):.4f}")
        return self.fittest.pieces


def solve_genetic(
    pieces: List[np.ndarray],
    rows: int,
    columns: int,
    contours: Optional[List[np.ndarray]] = None,
    **kwargs
) -> List[int]:
    solver = GeneticSolver(pieces, rows, columns, contours, **kwargs)
    return solver.solve()
