"""Backward-compatible imports; new work should import from ``src.eda``."""

try:
    from .eda import correlation_matrix, eda_summary, strongest_pairwise_correlation
except ImportError:  # Support direct imports when src/ itself is on sys.path.
    from eda import correlation_matrix, eda_summary, strongest_pairwise_correlation

__all__ = ["correlation_matrix", "eda_summary", "strongest_pairwise_correlation"]
