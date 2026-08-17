"""Market data dispatcher.

Routes each ticker to the right provider: BRVM tickers (the app's primary
market — see `app.brvm_reference`) go through the brvm.org/sikafinance
scraper, everything else falls back to Yahoo Finance. This lets a portfolio
that's mostly BRVM but holds a handful of international stocks still get
full valuation and performance data.

Benchmarks are always the BRVM indices (Composite, 30) — the relevant
reference for a BRVM-centric portfolio even when it holds a few foreign
lines.
"""
from __future__ import annotations

from datetime import date

import pandas as pd

from app import market_data_brvm as brvm
from app import market_data_yahoo as yahoo
from app.brvm_reference import is_brvm_ticker
from app.market_types import TickerInfo

__all__ = ["TickerInfo", "fetch_ticker_infos", "fetch_price_history", "fetch_benchmark_history"]


def fetch_ticker_infos(tickers: list[str]) -> dict[str, TickerInfo | None]:
    brvm_tickers = [t for t in tickers if is_brvm_ticker(t)]
    other_tickers = [t for t in tickers if not is_brvm_ticker(t)]

    result: dict[str, TickerInfo | None] = {}
    if brvm_tickers:
        result.update(brvm.fetch_ticker_infos(brvm_tickers))
    for ticker in other_tickers:
        result[ticker] = yahoo.fetch_ticker_info(ticker)
    return result


def fetch_price_history(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    brvm_tickers = [t for t in tickers if is_brvm_ticker(t)]
    other_tickers = [t for t in tickers if not is_brvm_ticker(t)]

    frames = []
    if brvm_tickers:
        frames.append(brvm.fetch_price_history(brvm_tickers, start, end))
    if other_tickers:
        frames.append(yahoo.fetch_price_history(other_tickers, start, end))

    frames = [f for f in frames if not f.empty]
    if not frames:
        return pd.DataFrame()
    if len(frames) == 1:
        return frames[0]
    return frames[0].join(frames[1], how="outer").ffill()


def fetch_benchmark_history(start: date, end: date) -> dict[str, pd.Series]:
    return brvm.fetch_benchmark_history(start, end)
