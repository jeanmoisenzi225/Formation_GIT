"""Market data access via yfinance.

Every call is defensive: a ticker that can't be resolved (unknown symbol,
delisted, network hiccup) never blows up the whole analysis — the caller
gets `None`/empty data back plus a warning is left for the UI to surface.
"""
from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

BENCHMARKS: dict[str, str] = {
    "CAC 40": "^FCHI",
    "S&P 500": "^GSPC",
    "MSCI World": "URTH",
}


class TickerInfo:
    def __init__(self, current_price: float | None, sector: str | None, country: str | None,
                 currency: str | None, pe_ratio: float | None, name: str | None):
        self.current_price = current_price
        self.sector = sector
        self.country = country
        self.currency = currency
        self.pe_ratio = pe_ratio
        self.name = name


def fetch_ticker_info(ticker: str) -> TickerInfo | None:
    t = yf.Ticker(ticker)

    # Price comes from the lightweight "fast_info"/chart endpoint first, since
    # the richer "info" endpoint (quoteSummary) is far more likely to be
    # rate-limited by Yahoo. A price-only result is still useful to the user.
    price: float | None = None
    try:
        fast = t.fast_info
        price = fast.get("lastPrice") if isinstance(fast, dict) else getattr(fast, "last_price", None)
    except Exception:
        price = None

    if price is None:
        try:
            hist = t.history(period="5d")
            if not hist.empty:
                price = float(hist["Close"].dropna().iloc[-1])
        except Exception:
            price = None

    info: dict = {}
    try:
        info = t.info or {}
        if price is None:
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    except Exception:
        info = {}

    if price is None:
        return None

    return TickerInfo(
        current_price=float(price),
        sector=info.get("sector"),
        country=info.get("country"),
        currency=info.get("currency"),
        pe_ratio=info.get("trailingPE"),
        name=info.get("shortName") or info.get("longName"),
    )


def fetch_price_history(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    """Return a DataFrame of daily close prices, columns=tickers, forward-filled."""
    if not tickers:
        return pd.DataFrame()
    try:
        data = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            progress=False,
            auto_adjust=True,
            group_by="ticker" if len(tickers) > 1 else None,
        )
    except Exception:
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    if len(tickers) == 1:
        closes = data["Close"].to_frame(name=tickers[0]) if "Close" in data else pd.DataFrame()
    else:
        closes = pd.DataFrame({tk: data[tk]["Close"] for tk in tickers if tk in data.columns.get_level_values(0)})

    return closes.ffill().dropna(how="all")


def fetch_benchmark_history(start: date, end: date) -> dict[str, pd.Series]:
    symbols = list(BENCHMARKS.values())
    history = fetch_price_history(symbols, start, end)
    result: dict[str, pd.Series] = {}
    for name, symbol in BENCHMARKS.items():
        if symbol in history.columns:
            result[name] = history[symbol].dropna()
    return result
