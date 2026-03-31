"""Ground truth data for validating extraction accuracy.

Hand-verified expected values for key companies, sourced from SEC EDGAR
XBRL filings and public records. Used as benchmarks to measure whether
extraction improvements (Phases 18-20) actually improve data quality.

Each company module exports a GROUND_TRUTH dict with 13 categories:
    identity, financials, market, governance, litigation, distress,
    item1_business, item7_mda, item8_footnotes, item9a_controls,
    eight_k_events, ownership, risk_factors

10 companies covering 5 industry verticals plus 2 known-outcome:
    TSLA (INDU), AAPL (TECH), JPM (FINS), NVDA (TECH), MRNA (HLTH),
    XOM (ENGY), PG (HLTH), DIS (UTIL), SMCI (TECH*), COIN (FINS*)
    * = known-outcome company

All financial values are in raw USD (not millions).
"""

from __future__ import annotations

from typing import Any

from tests.ground_truth.aapl import GROUND_TRUTH as AAPL_TRUTH
from tests.ground_truth.coin import GROUND_TRUTH as COIN_TRUTH
from tests.ground_truth.dis import GROUND_TRUTH as DIS_TRUTH
from tests.ground_truth.jpm import GROUND_TRUTH as JPM_TRUTH
from tests.ground_truth.mrna import GROUND_TRUTH as MRNA_TRUTH
from tests.ground_truth.nflx import GROUND_TRUTH as NFLX_TRUTH
from tests.ground_truth.nvda import GROUND_TRUTH as NVDA_TRUTH
from tests.ground_truth.pg import GROUND_TRUTH as PG_TRUTH
from tests.ground_truth.smci import GROUND_TRUTH as SMCI_TRUTH
from tests.ground_truth.tsla import GROUND_TRUTH as TSLA_TRUTH
from tests.ground_truth.xom import GROUND_TRUTH as XOM_TRUTH

ALL_GROUND_TRUTH: dict[str, dict[str, dict[str, Any]]] = {
    "TSLA": TSLA_TRUTH,
    "AAPL": AAPL_TRUTH,
    "JPM": JPM_TRUTH,
    "NVDA": NVDA_TRUTH,
    "MRNA": MRNA_TRUTH,
    "XOM": XOM_TRUTH,
    "PG": PG_TRUTH,
    "DIS": DIS_TRUTH,
    "SMCI": SMCI_TRUTH,
    "COIN": COIN_TRUTH,
    "NFLX": NFLX_TRUTH,
}

__all__ = [
    "AAPL_TRUTH",
    "ALL_GROUND_TRUTH",
    "COIN_TRUTH",
    "DIS_TRUTH",
    "JPM_TRUTH",
    "MRNA_TRUTH",
    "NFLX_TRUTH",
    "NVDA_TRUTH",
    "PG_TRUTH",
    "SMCI_TRUTH",
    "TSLA_TRUTH",
    "XOM_TRUTH",
]
