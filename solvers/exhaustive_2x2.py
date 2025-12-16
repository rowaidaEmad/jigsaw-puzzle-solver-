from itertools import permutations
import numpy as np
from utils.similarity import SimilarityCalculator

def solve_exhaustive_2x2(pieces_dict, similarity=None):
    """
    Exhaustively solve 2x2 by checking all 4! = 24 permutations.
    Returns arrangement list of length 4: [pos0, pos1, pos2, pos3]
    """
    sim = similarity or SimilarityCalculator()

    # piece ids are 0..3 (because n = rows*cols = 4)
    ids = [0, 1, 2, 3]

    # Precompute dissimilarities exactly like your other solvers:
    diss_h = np.full((4, 4), np.inf, dtype=np.float32)
    diss_v = np.full((4, 4), np.inf, dtype=np.float32)

    for i in ids:
        for j in ids:
            if i == j: 
                continue
            diss_h[i, j] = sim.compute(i, j, 3, pieces_dict)  # i -> right neighbor j
            diss_v[i, j] = sim.compute(i, j, 1, pieces_dict)  # i -> down neighbor j

    def cost(arr):
        # positions: [0 1]
        #            [2 3]
        a0, a1, a2, a3 = arr
        return float(diss_h[a0, a1] + diss_h[a2, a3] + diss_v[a0, a2] + diss_v[a1, a3])

    best_arr = None
    best_cost = float("inf")

    for perm in permutations(ids):
        c = cost(perm)
        if c < best_cost:
            best_cost = c
            best_arr = list(perm)

    return best_arr
