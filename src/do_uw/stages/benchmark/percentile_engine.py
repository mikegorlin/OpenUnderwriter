"""Percentile rank computation engine for peer benchmarking.

Provides the core statistical function for computing where a company
value falls within a distribution of peer values. Handles both
"higher is better" and "lower is better" metrics with proper tie handling.
"""

from __future__ import annotations


def percentile_rank(
    company_value: float,
    peer_values: list[float],
    *,
    higher_is_better: bool = True,
) -> float:
    """Compute percentile rank (0-100) of company_value within peer_values.

    Uses the standard percentile rank formula:
        rank = ((count_below + 0.5 * count_equal) / N) * 100

    For lower_is_better metrics (e.g., debt_to_equity, short_interest),
    the formula is flipped so the lowest value gets the highest percentile:
        rank = ((count_above + 0.5 * count_equal) / N) * 100

    Args:
        company_value: The subject company's metric value.
        peer_values: List of peer metric values for comparison.
        higher_is_better: If True, higher values get higher percentiles.
            If False, lower values get higher percentiles (flipped).

    Returns:
        Percentile rank from 0 to 100. Returns 50.0 if peer_values
        is empty (no comparison possible).
    """
    if not peer_values:
        return 50.0

    n = len(peer_values)

    if higher_is_better:
        count_below = sum(1 for v in peer_values if v < company_value)
        count_equal = sum(1 for v in peer_values if v == company_value)
    else:
        # For lower_is_better: count values ABOVE (they are worse)
        count_below = sum(1 for v in peer_values if v > company_value)
        count_equal = sum(1 for v in peer_values if v == company_value)

    return ((count_below + 0.5 * count_equal) / n) * 100.0


def ratio_to_baseline(
    company_value: float,
    baseline_value: float,
) -> float:
    """Compute ratio of company value to sector baseline.

    A ratio > 1.0 means the company exceeds the baseline.
    A ratio < 1.0 means the company is below the baseline.
    Returns 1.0 if baseline is zero (treated as equal to baseline).

    Args:
        company_value: The subject company's metric value.
        baseline_value: The sector baseline value.

    Returns:
        Ratio of company_value to baseline_value.
    """
    if baseline_value == 0.0:
        return 1.0
    return company_value / baseline_value


__all__ = ["percentile_rank", "ratio_to_baseline"]
