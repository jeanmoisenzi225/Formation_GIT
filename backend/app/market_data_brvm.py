"""Market data for BRVM-listed securities.

Two sources, since there is no official free BRVM API:

- brvm.org (official exchange site) for **today's** data: current quotes,
  sector classification, market capitalization. Plain server-rendered HTML
  tables, one request typically covers every listed ticker at once.
- sikafinance.com (private financial portal) for **historical** daily
  OHLCV, via an unofficial-but-public JSON endpoint
  (`POST /api/general/GetHistos`). That endpoint caps a single request to a
  3-month window, so longer ranges are paginated client-side.

Both are scraped defensively: any failure (network, layout change, rate
limiting) degrades to missing data for the affected ticker(s) rather than
failing the whole analysis — consistent with the rest of the app.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import httpx
import pandas as pd
from bs4 import BeautifulSoup

from app.brvm_reference import BENCHMARKS, SECTOR_PAGES, TICKERS, country_for, sika_symbol
from app.market_types import TickerInfo

USER_AGENT = "Mozilla/5.0 (compatible; PortfolioAnalyzer/1.0)"
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = 15.0
SIKA_MAX_WINDOW_DAYS = 85  # sikafinance rejects windows longer than ~3 months
MAX_WORKERS = 6


def _parse_fr_number(text: str | None) -> float | None:
    if text is None:
        return None
    cleaned = text.replace("\xa0", "").replace(" ", "").replace(" ", "").strip()
    cleaned = cleaned.rstrip("%").replace(",", ".")
    if not cleaned or cleaned in {"-", "—"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _find_table_by_header(soup: BeautifulSoup, header_contains: str):
    for table in soup.find_all("table"):
        head = table.find("thead")
        if head and header_contains.lower() in head.get_text(" ", strip=True).lower():
            return table
    return None


def fetch_current_quotes() -> dict[str, dict]:
    """Today's close price (or last traded price) for every BRVM equity."""
    try:
        resp = httpx.get("https://www.brvm.org/fr/cours-actions/0", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    table = _find_table_by_header(soup, "symbole")
    if table is None:
        return {}

    quotes: dict[str, dict] = {}
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        ticker = cells[0].get_text(strip=True)
        quotes[ticker] = {
            "name": cells[1].get_text(strip=True),
            "volume": _parse_fr_number(cells[2].get_text()),
            "prev_close": _parse_fr_number(cells[3].get_text()),
            "open": _parse_fr_number(cells[4].get_text()),
            "close": _parse_fr_number(cells[5].get_text()),
        }
    return quotes


def fetch_market_caps() -> dict[str, dict]:
    """Shares outstanding and market capitalization for every BRVM equity."""
    try:
        resp = httpx.get("https://www.brvm.org/fr/capitalisations/0", headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception:
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")
    table = _find_table_by_header(soup, "capitalisation globale")
    if table is None:
        return {}

    caps: dict[str, dict] = {}
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        ticker = cells[0].get_text(strip=True)
        caps[ticker] = {
            "shares_outstanding": _parse_fr_number(cells[2].get_text()),
            "market_cap": _parse_fr_number(cells[5].get_text()),
        }
    return caps


def fetch_sector_map() -> dict[str, str]:
    """ticker -> sector name, built from BRVM's per-sector listing pages."""
    sectors: dict[str, str] = {}

    def _load(sector_name: str, page_id: int) -> list[str]:
        try:
            resp = httpx.get(f"https://www.brvm.org/fr/cours-actions/{page_id}", headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
        except Exception:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        table = _find_table_by_header(soup, "symbole")
        if table is None:
            return []
        return [row.find("td").get_text(strip=True) for row in table.find("tbody").find_all("tr") if row.find("td")]

    with ThreadPoolExecutor(max_workers=len(SECTOR_PAGES)) as pool:
        futures = {pool.submit(_load, name, pid): name for name, pid in SECTOR_PAGES.items()}
        for future in as_completed(futures):
            sector_name = futures[future]
            for ticker in future.result():
                sectors[ticker] = sector_name

    return sectors


def fetch_ticker_infos(tickers: list[str]) -> dict[str, TickerInfo | None]:
    """Bulk fetch of quotes + market caps + sectors, composed into a
    TickerInfo per requested ticker. Only 1 + 1 + 7 HTTP requests total,
    regardless of how many tickers are requested.
    """
    with ThreadPoolExecutor(max_workers=3) as pool:
        quotes_future = pool.submit(fetch_current_quotes)
        caps_future = pool.submit(fetch_market_caps)
        sectors_future = pool.submit(fetch_sector_map)
        quotes = quotes_future.result()
        caps = caps_future.result()
        sectors = sectors_future.result()

    result: dict[str, TickerInfo | None] = {}
    for ticker in tickers:
        quote = quotes.get(ticker)
        if quote is None or quote.get("close") is None:
            result[ticker] = None
            continue
        result[ticker] = TickerInfo(
            current_price=quote["close"],
            sector=sectors.get(ticker),
            country=country_for(ticker),
            currency="XOF",
            pe_ratio=None,  # not published by brvm.org or sikafinance
            name=quote.get("name") or TICKERS.get(ticker, (None,))[0],
        )
    return result


def _date_chunks(start: date, end: date):
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=SIKA_MAX_WINDOW_DAYS), end)
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def _fetch_sika_history(symbol: str, start: date, end: date) -> pd.Series:
    frames: list[pd.Series] = []
    with httpx.Client(headers={**HEADERS, "Content-Type": "application/json;charset=UTF-8"}, timeout=TIMEOUT) as client:
        for chunk_start, chunk_end in _date_chunks(start, end):
            payload = {
                "ticker": symbol,
                "datedeb": chunk_start.isoformat(),
                "datefin": chunk_end.isoformat(),
                "xperiod": "0",
            }
            try:
                resp = client.post("https://www.sikafinance.com/api/general/GetHistos", json=payload)
                resp.raise_for_status()
                data = resp.json()
            except Exception:
                continue
            rows = data.get("lst")
            if not rows:
                continue
            dates = pd.to_datetime([r["Date"] for r in rows], format="%d/%m/%Y")
            closes = [r["Close"] for r in rows]
            frames.append(pd.Series(closes, index=dates))

    if not frames:
        return pd.Series(dtype=float)
    return pd.concat(frames).sort_index()


def fetch_price_history(tickers: list[str], start: date, end: date) -> pd.DataFrame:
    """Daily close prices for a list of BRVM tickers, one column each."""
    series: dict[str, pd.Series] = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {}
        for ticker in tickers:
            symbol = sika_symbol(ticker)
            if symbol is None:
                continue
            futures[pool.submit(_fetch_sika_history, symbol, start, end)] = ticker
        for future in as_completed(futures):
            ticker = futures[future]
            result = future.result()
            if not result.empty:
                series[ticker] = result

    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).ffill().dropna(how="all")


def fetch_benchmark_history(start: date, end: date) -> dict[str, pd.Series]:
    result: dict[str, pd.Series] = {}
    with ThreadPoolExecutor(max_workers=len(BENCHMARKS)) as pool:
        futures = {pool.submit(_fetch_sika_history, code, start, end): name for name, code in BENCHMARKS.items()}
        for future in as_completed(futures):
            name = futures[future]
            series = future.result()
            if not series.empty:
                result[name] = series
    return result
