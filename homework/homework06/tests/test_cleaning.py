"""Tests for the required Stage 06 cleaning functions."""

import unittest
from pathlib import Path
import sys

import pandas as pd

HOMEWORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOMEWORK_DIR))

from src.cleaning import drop_missing, fill_missing_median, normalize_data


class CleaningFunctionTests(unittest.TestCase):
    """Verify correctness, validation, and non-mutating behavior."""

    def test_fill_missing_median_fills_numeric_values_without_mutation(self):
        original = pd.DataFrame({"value": [1.0, None, 9.0], "label": ["a", "b", "c"]})
        cleaned = fill_missing_median(original, ["value"])

        self.assertTrue(original["value"].isna().any())
        self.assertEqual(cleaned.loc[1, "value"], 5.0)

    def test_fill_missing_median_rejects_non_numeric_column(self):
        with self.assertRaises(TypeError):
            fill_missing_median(pd.DataFrame({"label": ["a", None]}), ["label"])

    def test_drop_missing_removes_rows_for_required_subset(self):
        original = pd.DataFrame({"date": ["2025-01-01", None], "value": [None, 2.0]})
        cleaned = drop_missing(original, subset=["date"])

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(cleaned.loc[0, "date"], "2025-01-01")

    def test_drop_missing_threshold_removes_sparse_columns(self):
        original = pd.DataFrame({"keep": [1.0, None, 3.0], "drop": [None, None, 1.0]})
        cleaned = drop_missing(original, threshold=0.5)

        self.assertEqual(list(cleaned.columns), ["keep"])

    def test_normalize_data_minmax_and_zscore(self):
        original = pd.DataFrame({"value": [10.0, 20.0, 30.0]})
        minmax = normalize_data(original, ["value"], method="minmax", suffix="_minmax")
        zscore = normalize_data(original, ["value"], method="zscore", suffix="_zscore")

        self.assertEqual(minmax["value_minmax"].tolist(), [0.0, 0.5, 1.0])
        self.assertAlmostEqual(zscore["value_zscore"].mean(), 0.0)
        self.assertAlmostEqual(zscore["value_zscore"].std(ddof=0), 1.0)

    def test_normalize_data_maps_constant_column_to_zero(self):
        cleaned = normalize_data(pd.DataFrame({"value": [4.0, 4.0]}), ["value"])
        self.assertEqual(cleaned["value_normalized"].tolist(), [0.0, 0.0])


if __name__ == "__main__":
    unittest.main()
