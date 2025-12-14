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
    def __init__(self, output_dir: str, grid_size: str = "4x4"):
        self.output_dir = Path(output_dir)
        self.grid_size = grid_size
        self.tiles_dir = self.output_dir / f"tiles_{grid_size}"

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
