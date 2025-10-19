"""Utilities related to ticker symbol handling."""

from __future__ import annotations

from typing import Dict, Iterable, List

from ..config import YAHOO_TICKER_ALIASES


def resolve_yahoo_ticker(ticker: str) -> str:
    """Return the Yahoo Finance symbol to query for the given internal ticker."""
    return YAHOO_TICKER_ALIASES.get(ticker, ticker)


def translate_missing_aliases(
    missing_aliases: Iterable[str],
    alias_map: Dict[str, List[str]] | None = None,
) -> List[str]:
    """Map Yahoo aliases back to the original tickers when possible."""
    resolved: List[str] = []

    for alias in missing_aliases:
        originals: List[str] = []

        if alias_map and alias in alias_map:
            originals.extend(alias_map[alias])

        mapped = [original for original, target in YAHOO_TICKER_ALIASES.items() if target == alias]
        originals.extend(mapped)

        if originals:
            resolved.extend(sorted(set(originals)))
        else:
            resolved.append(alias)

    return resolved
