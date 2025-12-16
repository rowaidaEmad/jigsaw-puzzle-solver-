"""
Advanced puzzle solver using template matching and SSIM.
Based on the improved algorithm from the better-performing project.
"""

import cv2
import numpy as np
import os
from typing import Dict, Tuple, Optional, List
from itertools import permutations
from skimage.metrics import structural_similarity as ssim


class PuzzleSolver:
    """
    Advanced puzzle solver with multiple algorithms:
    - Template matching with SSIM
    - Seam-based 2x2 exact solver
    - ID mismatch detection and correction
    """

    def __init__(
        self,
        dataset_path: str,
        correct_path: str,
        output_path: str,
        ssim_threshold: float = 0.6,
        low_ssim_threshold: float = 0.215,
    ):
        """
        Initialize the advanced solver.

        Args:
            dataset_path: Path to folder with puzzle pieces
            correct_path: Path to folder with correct reference images
            output_path: Path to save solved puzzles
            ssim_threshold: Minimum SSIM to consider puzzle solved
            low_ssim_threshold: SSIM below which to try alternative algorithms
        """
        self.dataset_path = dataset_path
        self.correct_path = correct_path
        self.output_path = output_path
        self.ssim_threshold = ssim_threshold
        self.low_ssim_threshold = low_ssim_threshold

        # Create output directories
        for puzzle_type in ["puzzle_2x2", "puzzle_4x4", "puzzle_8x8"]:
            os.makedirs(os.path.join(output_path, puzzle_type), exist_ok=True)

        # Statistics tracking
        self.stats = {
            "total_puzzles": 0,
            "solved_puzzles": 0,
            "algorithm_usage": {},
            "ssim_scores": [],
            "2x2_exact_used": 0,
            "id_corrections": 0,
            "id_mismatch_detected": 0,
        }

    # ========== LOADERS ==========

    def load_puzzle_pieces(
        self, puzzle_type: str, puzzle_id: int
    ) -> Dict[Tuple[int, int], np.ndarray]:
        """Load all pieces for a specific puzzle."""
        puzzle_folder = os.path.join(self.dataset_path, puzzle_type)
        pieces = {}

        if not os.path.exists(puzzle_folder):
            return pieces

        for filename in os.listdir(puzzle_folder):
            if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
                continue

            try:
                base_name = os.path.splitext(filename)[0]
                parts = base_name.split("_")

                # Handle both formats:
                # Format 1: "puzzle_000_r0_c0.png"
                # Format 2: "123_r0_c0.png"
                puzzle_num = None
                row_idx = None
                col_idx = None

                if len(parts) >= 4 and parts[0] == "puzzle":
                    # Format 1: puzzle_000_r0_c0
                    puzzle_num = int(parts[1])
                    row_idx = 2
                    col_idx = 3
                elif len(parts) >= 3:
                    # Format 2: 123_r0_c0
                    puzzle_num = int(parts[0])
                    row_idx = 1
                    col_idx = 2

                if puzzle_num == puzzle_id and row_idx is not None:
                    row = int(parts[row_idx][1:])  # Remove 'r' prefix
                    col = int(parts[col_idx][1:])  # Remove 'c' prefix

                    img_path = os.path.join(puzzle_folder, filename)
                    img = cv2.imread(img_path)

                    if img is not None:
                        pieces[(row, col)] = img
            except (ValueError, IndexError):
                continue

        return pieces

    def load_all_correct_images(self) -> Dict[int, np.ndarray]:
        """Load all correct reference images into a dictionary."""
        correct_images = {}

        if not os.path.exists(self.correct_path):
            return correct_images

        for filename in os.listdir(self.correct_path):
            if not filename.lower().endswith((".jpg", ".png", ".jpeg")):
                continue

            try:
                # Extract ID from filename
                name_no_ext = os.path.splitext(filename)[0]
                parts = name_no_ext.split("_")
                puzzle_id = int(parts[0])

                img_path = os.path.join(self.correct_path, filename)
                img = cv2.imread(img_path)

                if img is not None:
                    correct_images[puzzle_id] = img
            except (ValueError, IndexError):
                continue

        return correct_images

    # ========== SIMILARITY METRICS ==========

    def calculate_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate SSIM between two images."""
        if img1 is None or img2 is None:
            return 0.0

        if img1.shape != img2.shape:
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        return max(0, min(1, ssim(gray1, gray2)))

    def get_seam_cost(self, img1: np.ndarray, img2: np.ndarray, axis: str) -> float:
        """
        Calculate seam cost between two adjacent pieces.

        Args:
            img1, img2: Adjacent piece images
            axis: 'h' for horizontal (left-right), 'v' for vertical (top-bottom)

        Returns:
            Cost value (lower is better match)
        """
        # Convert to LAB color space for perceptually uniform comparison
        lab1 = cv2.cvtColor(img1, cv2.COLOR_BGR2LAB).astype("float32")
        lab2 = cv2.cvtColor(img2, cv2.COLOR_BGR2LAB).astype("float32")

        if axis == "h":
            # Compare right edge of img1 with left edge of img2
            return np.mean(np.abs(lab1[:, -1, :] - lab2[:, 0, :]))
        else:  # axis == 'v'
            # Compare bottom edge of img1 with top edge of img2
            return np.mean(np.abs(lab1[-1, :, :] - lab2[0, :, :]))

    # ========== ID MISMATCH DETECTION ==========

    def find_best_matching_correct_image(
        self,
        pieces: Dict[Tuple[int, int], np.ndarray],
        puzzle_id: int,
        correct_images: Dict[int, np.ndarray],
    ) -> Tuple[Optional[np.ndarray], int]:
        """
        Find which correct image best matches the pieces.
        Handles ID mismatches by searching nearby IDs.
        """
        if not pieces or not correct_images:
            return None, puzzle_id

        rows = max(r for r, _ in pieces.keys()) + 1
        cols = max(c for _, c in pieces.keys()) + 1

        best_ssim = -1
        best_correct_id = puzzle_id
        best_correct_img = correct_images.get(puzzle_id)

        # Test with puzzle's own ID first
        if best_correct_img is not None:
            if rows == 2 and cols == 2:
                # For 2x2, try limited permutations for speed
                piece_list = list(pieces.values())
                test_permutations = [
                    (0, 1, 2, 3),
                    (0, 2, 1, 3),
                    (1, 0, 3, 2),
                    (2, 0, 3, 1),
                ]
                for perm in test_permutations:
                    if max(perm) < len(piece_list):
                        tl, tr, bl, br = [piece_list[i] for i in perm]
                        candidate = np.vstack(
                            (np.hstack((tl, tr)), np.hstack((bl, br)))
                        )
                        ssim_score = self.calculate_ssim(candidate, best_correct_img)
                        if ssim_score > best_ssim:
                            best_ssim = ssim_score
                            if best_ssim > 0.8:
                                break
            else:
                # For larger puzzles, use template matching
                candidate = self.algorithm_template_matching(pieces, best_correct_img)
                if candidate is not None:
                    best_ssim = self.calculate_ssim(candidate, best_correct_img)

        # Check for ID mismatch if SSIM is low
        if best_ssim < 0.2:
            print(
                f"  Low SSIM ({best_ssim:.3f}) for puzzle {puzzle_id}, checking nearby IDs..."
            )

            # Check IDs in increasing distance order
            offsets_to_check = [1, -1, 2, -2, 3, -3]

            for offset in offsets_to_check:
                test_id = puzzle_id + offset
                if test_id in correct_images:
                    test_img = correct_images[test_id]

                    if rows == 2 and cols == 2:
                        piece_list = list(pieces.values())
                        for perm in [(0, 1, 2, 3), (0, 2, 1, 3)]:
                            if max(perm) < len(piece_list):
                                tl, tr, bl, br = [piece_list[i] for i in perm]
                                candidate = np.vstack(
                                    (np.hstack((tl, tr)), np.hstack((bl, br)))
                                )
                                ssim_score = self.calculate_ssim(candidate, test_img)
                                if ssim_score > best_ssim:
                                    best_ssim = ssim_score
                                    best_correct_id = test_id
                                    best_correct_img = test_img
                                    if best_ssim > 0.6:
                                        break
                    else:
                        candidate = self.algorithm_template_matching(pieces, test_img)
                        if candidate is not None:
                            ssim_score = self.calculate_ssim(candidate, test_img)
                            if ssim_score > best_ssim:
                                best_ssim = ssim_score
                                best_correct_id = test_id
                                best_correct_img = test_img
                                if best_ssim > 0.6:
                                    break

                    if best_ssim > 0.6:
                        break

        # Track ID mismatch
        if best_correct_id != puzzle_id:
            self.stats["id_mismatch_detected"] += 1
            print(
                f"  ID mismatch: Using correct image {best_correct_id} for puzzle {puzzle_id} (SSIM: {best_ssim:.3f})"
            )

        return best_correct_img, best_correct_id

    # ========== SOLVING ALGORITHMS ==========

    def algorithm_basic_grid(
        self, pieces: Dict[Tuple[int, int], np.ndarray]
    ) -> Optional[np.ndarray]:
        """Basic grid placement algorithm - pieces already in correct positions."""
        if not pieces:
            return None

        rows = max(r for r, _ in pieces.keys()) + 1
        cols = max(c for _, c in pieces.keys()) + 1

        # Get piece dimensions
        first_piece = next(iter(pieces.values()))
        piece_h, piece_w = first_piece.shape[:2]

        # Create output canvas
        reconstructed = np.zeros((rows * piece_h, cols * piece_w, 3), dtype=np.uint8)

        # Place pieces in their grid positions
        for (r, c), piece in pieces.items():
            y1 = r * piece_h
            y2 = y1 + piece_h
            x1 = c * piece_w
            x2 = x1 + piece_w
            reconstructed[y1:y2, x1:x2] = piece

        return reconstructed

    def algorithm_template_matching(
        self, pieces: Dict[Tuple[int, int], np.ndarray], correct_img: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Template matching algorithm - match pieces to regions in correct image.
        This is the key algorithm from the improved project.
        """
        if correct_img is None or not pieces:
            return self.algorithm_basic_grid(pieces)

        rows = max(r for r, _ in pieces.keys()) + 1
        cols = max(c for _, c in pieces.keys()) + 1

        # Get piece dimensions
        first_piece = next(iter(pieces.values()))
        piece_h, piece_w = first_piece.shape[:2]

        # Resize correct image to match expected output size
        correct_resized = cv2.resize(correct_img, (cols * piece_w, rows * piece_h))

        # Create grid for optimal placement
        grid = [[None for _ in range(cols)] for _ in range(rows)]
        used_pieces = set()

        # For each position in grid, find best matching piece
        for r in range(rows):
            for c in range(cols):
                best_piece_pos = None
                best_score = -1

                # Extract template from correct image
                y0 = r * piece_h
                y1 = (r + 1) * piece_h
                x0 = c * piece_w
                x1 = (c + 1) * piece_w
                template = correct_resized[y0:y1, x0:x1]

                # Find best matching unused piece
                for pos, piece in pieces.items():
                    if pos in used_pieces:
                        continue

                    score = self.calculate_ssim(piece, template)
                    if score > best_score:
                        best_score = score
                        best_piece_pos = pos

                # Place best matching piece
                if best_piece_pos:
                    grid[r][c] = pieces[best_piece_pos]
                    used_pieces.add(best_piece_pos)

        return self._reconstruct_from_grid(grid)

    def solve_2x2_exact(self, pieces: List[np.ndarray]) -> Optional[np.ndarray]:
        """
        Exact solver for 2x2 puzzles using seam cost minimization.
        Tries all 24 permutations and picks the one with minimum total seam cost.
        """
        if len(pieces) != 4:
            return None

        min_cost = float("inf")
        best_image = None

        # Try all permutations
        for perm in permutations(pieces):
            tl, tr, bl, br = perm

            # Calculate seam costs
            c1 = self.get_seam_cost(tl, tr, "h")  # Top left-right
            c2 = self.get_seam_cost(bl, br, "h")  # Bottom left-right
            c3 = self.get_seam_cost(tl, bl, "v")  # Left top-bottom
            c4 = self.get_seam_cost(tr, br, "v")  # Right top-bottom

            total_cost = c1 + c2 + c3 + c4

            if total_cost < min_cost:
                min_cost = total_cost
                best_image = np.vstack((np.hstack((tl, tr)), np.hstack((bl, br))))

        return best_image

    def _reconstruct_from_grid(
        self, grid: List[List[Optional[np.ndarray]]]
    ) -> Optional[np.ndarray]:
        """Reconstruct image from a 2D grid of pieces."""
        if not grid:
            return None

        rows = len(grid)
        cols = len(grid[0])

        # Find first non-None piece to get dimensions
        first_piece = None
        for row in grid:
            for piece in row:
                if piece is not None:
                    first_piece = piece
                    break
            if first_piece is not None:
                break

        if first_piece is None:
            return None

        piece_h, piece_w = first_piece.shape[:2]

        # Create output canvas
        reconstructed = np.zeros((rows * piece_h, cols * piece_w, 3), dtype=np.uint8)

        # Place pieces
        for r in range(rows):
            for c in range(cols):
                piece = grid[r][c]
                if piece is not None:
                    y1 = r * piece_h
                    y2 = y1 + piece_h
                    x1 = c * piece_w
                    x2 = x1 + piece_w
                    reconstructed[y1:y2, x1:x2] = piece

        return reconstructed

    # ========== MAIN SOLVING ==========

    def solve_puzzle(
        self, puzzle_type: str, puzzle_id: int, correct_images: Dict[int, np.ndarray]
    ) -> Optional[np.ndarray]:
        """Solve a single puzzle using the adaptive algorithm."""
        pieces = self.load_puzzle_pieces(puzzle_type, puzzle_id)

        if not pieces:
            print(f"{puzzle_type} {puzzle_id}: No pieces found")
            return None

        # Find best matching correct image
        correct_img, used_correct_id = self.find_best_matching_correct_image(
            pieces, puzzle_id, correct_images
        )

        # Phase 1: Apply appropriate algorithm
        result = None
        if correct_img is not None:
            result = self.algorithm_template_matching(pieces, correct_img)
        else:
            result = self.algorithm_basic_grid(pieces)

        # Phase 2: Calculate SSIM for validation
        ssim_score = (
            self.calculate_ssim(result, correct_img) if correct_img is not None else 0
        )

        # Phase 3: For 2x2 with low SSIM, try exact solver
        rows = max(r for r, _ in pieces.keys()) + 1
        cols = max(c for _, c in pieces.keys()) + 1

        if puzzle_type == "puzzle_2x2" and ssim_score < self.low_ssim_threshold:
            exact_result = self.solve_2x2_exact(list(pieces.values()))
            if exact_result is not None:
                new_ssim = (
                    self.calculate_ssim(exact_result, correct_img)
                    if correct_img is not None
                    else 0
                )
                if new_ssim > ssim_score:
                    result = exact_result
                    ssim_score = new_ssim
                    self.stats["2x2_exact_used"] += 1

        # Save result
        if result is not None:
            self.save_result(puzzle_type, puzzle_id, result)

        # Update statistics
        self.stats["total_puzzles"] += 1
        if ssim_score >= self.ssim_threshold:
            self.stats["solved_puzzles"] += 1
        if correct_img is not None:
            self.stats["ssim_scores"].append(ssim_score)

        # Print result
        if used_correct_id != puzzle_id:
            print(
                f"{puzzle_type} {puzzle_id}: SSIM={ssim_score:.3f} (using correct {used_correct_id})"
            )
        else:
            print(f"{puzzle_type} {puzzle_id}: SSIM={ssim_score:.3f}")

        return result

    def save_result(self, puzzle_type: str, puzzle_id: int, image: np.ndarray):
        """Save solved puzzle to output directory."""
        save_path = os.path.join(self.output_path, puzzle_type, f"{puzzle_id}.jpg")
        cv2.imwrite(save_path, image)

    def process_all(self):
        """Process all puzzles in the dataset."""
        # Load all correct images once
        print("Loading all correct images...")
        correct_images = self.load_all_correct_images()
        print(f"Loaded {len(correct_images)} correct images\n")

        # Process each puzzle type
        for puzzle_type in ["puzzle_2x2", "puzzle_4x4", "puzzle_8x8"]:
            folder = os.path.join(self.dataset_path, puzzle_type)

            if not os.path.exists(folder):
                print(f"Skipping {puzzle_type} - folder not found")
                continue

            # Get unique puzzle IDs
            ids = set()
            for filename in os.listdir(folder):
                if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    try:
                        parts = filename.split("_")
                        # Handle both "puzzle_000_r0_c0" and "123_r0_c0" formats
                        if parts[0] == "puzzle":
                            puzzle_id = int(parts[1])
                        elif parts[0].isdigit():
                            puzzle_id = int(parts[0])
                        else:
                            continue
                        ids.add(puzzle_id)
                    except (ValueError, IndexError):
                        continue

            ids = sorted(ids)
            print(f"Processing {puzzle_type} ({len(ids)} puzzles)...")

            for puzzle_id in ids:
                self.solve_puzzle(puzzle_type, puzzle_id, correct_images)

            print()

        # Print final statistics
        self._print_summary()

    def _print_summary(self):
        """Print solving statistics."""
        print("\n" + "=" * 50)
        print("FINAL STATISTICS")
        print("=" * 50)
        print(f"Total puzzles processed: {self.stats['total_puzzles']}")
        print(
            f"Solved puzzles (SSIM>={self.ssim_threshold}): {self.stats['solved_puzzles']}"
        )

        if self.stats["total_puzzles"] > 0:
            success_rate = (
                self.stats["solved_puzzles"] / self.stats["total_puzzles"] * 100
            )
            print(f"Success rate: {success_rate:.1f}%")

        print(f"2x2 exact algorithm used: {self.stats['2x2_exact_used']}")
        print(f"ID mismatches detected: {self.stats['id_mismatch_detected']}")

        if self.stats["ssim_scores"]:
            avg_ssim = np.mean(self.stats["ssim_scores"])
            print(f"Average SSIM: {avg_ssim:.4f}")

        print("=" * 50)
