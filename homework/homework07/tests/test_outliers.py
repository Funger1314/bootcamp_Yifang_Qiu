"""Unit tests for the required Stage 07 outlier functions."""

import inspect
from pathlib import Path
import sys
import unittest

import pandas as pd

HOMEWORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOMEWORK_DIR))

from src.outliers import (
    detect_outliers_iqr,
    detect_outliers_zscore,
    iqr_bounds,
    winsorize_series,
)


class OutlierFunctionTests(unittest.TestCase):
    """Verify signatures, edge cases, and non-mutating behavior."""

    def test_required_function_signatures_are_starter_compatible(self):
        self.assertEqual(list(inspect.signature(detect_outliers_iqr).parameters), ["series", "k"])
        self.assertEqual(
            list(inspect.signature(detect_outliers_zscore).parameters),
            ["series", "threshold"],
        )
        self.assertEqual(
            list(inspect.signature(winsorize_series).parameters),
            ["series", "lower", "upper"],
        )

    def test_iqr_flags_extreme_and_preserves_index(self):
        series = pd.Series([1.0, 2.0, 2.0, 3.0, 100.0], index=list("abcde"))
        mask = detect_outliers_iqr(series, k=1.5)
        self.assertEqual(mask.tolist(), [False, False, False, False, True])
        self.assertEqual(mask.index.tolist(), series.index.tolist())

    def test_iqr_bounds_ignore_missing_and_missing_is_not_flagged(self):
        series = pd.Series([1.0, 2.0, None, 3.0, 100.0])
        lower, upper = iqr_bounds(series)
        mask = detect_outliers_iqr(series)
        self.assertLess(lower, upper)
        self.assertFalse(mask.iloc[2])

    def test_invalid_iqr_multiplier_is_rejected(self):
        with self.assertRaises(ValueError):
            detect_outliers_iqr(pd.Series([1.0, 2.0]), k=0)

    def test_zscore_flags_extreme_value(self):
        series = pd.Series([0.0] * 20 + [100.0])
        self.assertEqual(int(detect_outliers_zscore(series, threshold=3.0).sum()), 1)

    def test_zscore_constant_series_returns_false(self):
        mask = detect_outliers_zscore(pd.Series([4.0, 4.0, 4.0]))
        self.assertEqual(mask.tolist(), [False, False, False])

    def test_invalid_zscore_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            detect_outliers_zscore(pd.Series([1.0, 2.0]), threshold=-1)

    def test_empty_all_missing_and_non_numeric_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            detect_outliers_iqr(pd.Series([], dtype=float))
        with self.assertRaises(ValueError):
            detect_outliers_iqr(pd.Series([None], dtype=float))
        with self.assertRaises(TypeError):
            detect_outliers_iqr(pd.Series(["a", "b"]))

    def test_winsorize_clips_without_mutating_input(self):
        original = pd.Series([0.0, 1.0, 2.0, 100.0])
        result = winsorize_series(original, lower=0.25, upper=0.75)
        self.assertEqual(original.tolist(), [0.0, 1.0, 2.0, 100.0])
        self.assertGreater(result.iloc[0], original.iloc[0])
        self.assertLess(result.iloc[-1], original.iloc[-1])

    def test_invalid_winsor_quantiles_are_rejected(self):
        series = pd.Series([1.0, 2.0, 3.0])
        with self.assertRaises(ValueError):
            winsorize_series(series, lower=0.8, upper=0.2)
        with self.assertRaises(ValueError):
            winsorize_series(series, lower=-0.1, upper=0.9)


if __name__ == "__main__":
    unittest.main()
