import os
import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path


def load_piece(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Failed to load image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


class PieceLoader:
    def __init__(self, tiles_dir: str, grid_size: str = "4x4"):
        """Initialize loader.

        This class now treats the provided `tiles_dir` as the exact directory
        containing the subfolders (original, prep, upscaled, binary, edges,
        contours). It does no searching or guessing — if folders are missing it
        raises an error. This keeps behavior explicit and predictable.

        Args:
            tiles_dir: Exact path to tiles directory (must contain required subfolders).
            grid_size: Grid string like '4x4'.
        """
        self.tiles_dir = Path(tiles_dir)
        self.grid_size = grid_size

        # Verify the minimal expected structure
        required = ["original", "prep", "upscaled", "binary", "edges", "contours"]
        missing = [d for d in required if not (self.tiles_dir / d).exists()]
        if missing:
            raise ValueError(
                f"Tiles directory {self.tiles_dir} is missing expected folders: {missing}"
            )

        rows, cols = map(int, grid_size.split("x"))
        self.rows = rows
        self.cols = cols

    def get_puzzle_ids(self) -> List[int]:
        original_dir = self.tiles_dir / "original"
        if not original_dir.exists():
            return []

        ids = set()
        for f in original_dir.iterdir():
            if f.suffix == ".png":
                parts = f.stem.split("_")
                if len(parts) >= 2:
                    try:
                        ids.add(int(parts[1]))
                    except ValueError:
                        pass
        return sorted(ids)

    def _get_piece_path(self, folder: str, puzzle_id: int, row: int, col: int) -> str:
        return str(
            self.tiles_dir / folder / f"puzzle_{puzzle_id:03d}_r{row}_c{col}.png"
        )

    def load_puzzle_pieces(
        self, puzzle_id: int, piece_type: str = "original"
    ) -> List[np.ndarray]:
        """
        Load all pieces for a puzzle.
        piece_type: original, prep, upscaled, binary, edges, contours
        """
        pieces = []
        for r in range(self.rows):
            for c in range(self.cols):
                path = self._get_piece_path(piece_type, puzzle_id, r, c)
                pieces.append(load_piece(path))
        return pieces

    def load_with_contours(
        self, puzzle_id: int, piece_type: str = "original"
    ) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Load pieces and their contour versions."""
        pieces = self.load_puzzle_pieces(puzzle_id, piece_type)
        contours = self.load_puzzle_pieces(puzzle_id, "contours")
        return pieces, contours

    def load_all_types(self, puzzle_id: int) -> Dict[str, List[np.ndarray]]:
        """Load all available piece types for a puzzle."""
        types = {}
        for t in ["original", "prep", "upscaled", "binary", "edges", "contours"]:
            folder = self.tiles_dir / t
            if folder.exists():
                try:
                    types[t] = self.load_puzzle_pieces(puzzle_id, t)
                except Exception:
                    pass
        return types
