#!/usr/bin/env python3
"""Simple image directory comparator.

Compares images in two directories by basename. For each common file, the
script checks that images have the same shape and that the fraction of
pixels that differ (per-channel) is <= allowed fraction. It prints mismatches
and an overall accuracy percentage.

Usage:
  python scripts/compare_dirs_simple.py <expected_dir> <produced_dir> [--ext png] [--tolerance 0] [--max-diff-frac 0.0] [--max-delta 170]

This script intentionally stays small and predictable (no fancy heuristics).
"""

from pathlib import Path
import argparse
import cv2
import numpy as np
from typing import Tuple


def load_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to load image: {path}")
    # Normalize to RGB 3-channel
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
    else:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def compare_images(
    a: np.ndarray,
    b: np.ndarray,
    tolerance: int = 0,
    max_diff_frac: float = 0.0,
    max_delta_threshold: int = 170,
) -> Tuple[bool, dict]:
    """Return (match, metrics).

    - tolerance: per-channel pixel delta allowed.
    - max_diff_frac: allowed fraction of pixels exceeding tolerance.
    - max_delta_threshold: if observed max channel delta exceeds this, treat as mismatch.
    """
    if a.shape != b.shape:
        return False, {
            "reason": "shape_mismatch",
            "shape_a": a.shape,
            "shape_b": b.shape,
        }

    diff = np.abs(a.astype(np.int32) - b.astype(np.int32))
    max_delta = int(diff.max())
    frac_diff = float(np.mean(np.any(diff > tolerance, axis=2)))

    # Max-delta override: if any channel delta exceeds threshold, fail
    if max_delta > max_delta_threshold:
        return False, {"reason": "max_delta_exceeded", "max_delta": max_delta}

    ok = frac_diff <= max_diff_frac
    metrics = {"max_delta": max_delta, "frac_diff": frac_diff}
    return ok, metrics


def main():
    parser = argparse.ArgumentParser(description="Simple image directory comparator")
    parser.add_argument("expected", help="Expected images directory")
    parser.add_argument("produced", help="Produced images directory")
    parser.add_argument(
        "--ext", default="png", help="File extension to compare (default: png)"
    )
    parser.add_argument(
        "--tolerance",
        type=int,
        default=0,
        help="Per-channel pixel tolerance (default: 0 - exact)",
    )
    parser.add_argument(
        "--max-diff-frac",
        type=float,
        default=1,
        help="Allowed fraction of pixels differing (default: 1)",
    )
    parser.add_argument(
        "--max-delta",
        type=int,
        default=170,
        help="Max channel delta threshold that forces mismatch (default: 170)",
    )
    args = parser.parse_args()

    d1 = Path(args.expected)
    d2 = Path(args.produced)
    files1 = {p.name: p for p in sorted(d1.glob(f"*.{args.ext}"))}
    files2 = {p.name: p for p in sorted(d2.glob(f"*.{args.ext}"))}

    common = sorted(set(files1.keys()) & set(files2.keys()))
    only1 = sorted(set(files1.keys()) - set(files2.keys()))
    only2 = sorted(set(files2.keys()) - set(files1.keys()))

    if only1:
        print(f"Only in expected ({d1}): {len(only1)} (first: {only1[:5]})")
    if only2:
        print(f"Only in produced ({d2}): {len(only2)} (first: {only2[:5]})")

    if not common:
        print("No common files to compare. Exiting.")
        return

    mismatches = []
    for name in common:
        p1 = files1[name]
        p2 = files2[name]
        try:
            a = load_image(p1)
            b = load_image(p2)
        except Exception as e:
            mismatches.append((name, f"load_error: {e}"))
            continue

        ok, metrics = compare_images(
            a,
            b,
            tolerance=args.tolerance,
            max_diff_frac=args.max_diff_frac,
            max_delta_threshold=args.max_delta,
        )
        if not ok:
            mismatches.append((name, metrics))

    total = len(common)
    failed = len(mismatches)
    passed = total - failed

    for name, reason in mismatches:
        print(f"MISMATCH: {name} -> {reason}")

    acc = 100.0 * passed / total if total else 0.0
    print(
        f"\nCompared {total} images: {passed} passed, {failed} failed. Accuracy: {acc:.2f}%"
    )


if __name__ == "__main__":
    main()
