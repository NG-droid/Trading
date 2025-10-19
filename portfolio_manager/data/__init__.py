"""Data package containing static resources (dividends reference, etc.)."""

from .dividends_reference import DIVIDEND_FALLBACKS  # re-export for convenience

__all__ = ["DIVIDEND_FALLBACKS"]
