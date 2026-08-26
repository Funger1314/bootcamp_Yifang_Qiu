"""Unit tests for the required Stage 08 EDA helpers."""

from pathlib import Path
import sys
import unittest

import pandas as pd

HOMEWORK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOMEWORK_DIR))

from src.eda import correlation_matrix, eda_summary, strongest_pairwise_correlation


class EdaHelperTests(unittest.TestCase):
    """Verify profiling completeness, correlation behavior, and non-mutation."""

    def setUp(self):
        self.data = pd.DataFrame(
            {
                "value": [1.0, 2.0, 3.0, 100.0],
                "second": [4.0, 3.0, 2.0, 1.0],
                "group": pd.Series(["a", "a", "b", "b"], dtype="category"),
            }
        )

    def test_eda_summary_profiles_numeric_and_categorical_columns(self):
        result = eda_summary(self.data)
        self.assertEqual(result["shape"], (4, 3))
        self.assertIn("value", result["numeric_profile"].index)
        self.assertIn("group", result["categorical_profile"])
        self.assertEqual(result["categorical_profile"]["group"].loc["a", "count"], 2)
        self.assertAlmostEqual(
            result["categorical_profile"]["group"].loc["a", "proportion"], 0.5
        )

    def test_eda_summary_does_not_mutate_input(self):
        original = self.data.copy(deep=True)
        eda_summary(self.data)
        pd.testing.assert_frame_equal(self.data, original)

    def test_strongest_correlation_handles_read_only_backing_array(self):
        correlation = correlation_matrix(self.data, ["value", "second"])
        correlation.to_numpy(copy=False).flags.writeable = False
        left, right, strength = strongest_pairwise_correlation(correlation)
        self.assertEqual({left, right}, {"value", "second"})
        self.assertLess(strength, 0)


if __name__ == "__main__":
    unittest.main()
