"""Portfolio analytics: valuation, allocation, performance vs benchmarks and
risk metrics. All computations are done with plain pandas/numpy so they stay
easy to unit test without hitting the network.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from app.market_data import TickerInfo, fetch_benchmark_history, fetch_price_history, fetch_ticker_info
from app.portfolio import PortfolioState
from app.schemas import (
    AllocationSlice,
    PerformancePoint,
    Position,
    PortfolioSummary,
    RiskMetrics,
    Transaction,
)

RISK_FREE_RATE = 0.02  # annualized, used for the Sharpe ratio
TRADING_DAYS_PER_YEAR = 252


def build_positions_with_market_data(state: PortfolioState) -> tuple[list[Position], list[str]]:
    warnings: list[str] = []
    positions: list[Position] = []

    total_value = 0.0
    infos: dict[str, TickerInfo | None] = {ticker: fetch_ticker_info(ticker) for ticker in state.lots}

    provisional: list[tuple[str, Position, float]] = []
    for ticker, lot in state.lots.items():
        info = infos.get(ticker)
        cost_basis = lot.average_cost * lot.quantity
        if info is None:
            warnings.append(f"Données de marché indisponibles pour {ticker} (position affichée au coût d'achat).")
            pos = Position(
                ticker=ticker,
                label=lot.label,
                quantity=lot.quantity,
                average_cost=lot.average_cost,
                cost_basis=cost_basis,
                market_data_available=False,
            )
            provisional.append((ticker, pos, 0.0))
            continue

        current_value = info.current_price * lot.quantity
        unrealized_gain = current_value - cost_basis
        pos = Position(
            ticker=ticker,
            label=lot.label or info.name,
            quantity=lot.quantity,
            average_cost=lot.average_cost,
            cost_basis=cost_basis,
            current_price=info.current_price,
            current_value=current_value,
            unrealized_gain=unrealized_gain,
            unrealized_gain_pct=(unrealized_gain / cost_basis * 100) if cost_basis else None,
            sector=info.sector,
            country=info.country,
            currency=info.currency,
            pe_ratio=info.pe_ratio,
            market_data_available=True,
        )
        provisional.append((ticker, pos, current_value))
        total_value += current_value

    for ticker, pos, value in provisional:
        pos.weight_pct = (value / total_value * 100) if total_value else None
        positions.append(pos)

    positions.sort(key=lambda p: p.current_value or p.cost_basis, reverse=True)
    return positions, warnings


def build_summary(transactions: list[Transaction], state: PortfolioState, positions: list[Position]) -> PortfolioSummary:
    total_cost_basis = sum(p.cost_basis for p in positions)
    total_current_value = sum(p.current_value or p.cost_basis for p in positions)
    total_unrealized_gain = total_current_value - total_cost_basis
    return PortfolioSummary(
        total_cost_basis=total_cost_basis,
        total_current_value=total_current_value,
        total_unrealized_gain=total_unrealized_gain,
        total_unrealized_gain_pct=(total_unrealized_gain / total_cost_basis * 100) if total_cost_basis else 0.0,
        realized_gain=state.total_realized_gain,
        total_dividends=state.total_dividends,
        total_fees=state.total_fees,
        positions_count=len(positions),
        as_of=date.today(),
    )


def _allocation(positions: list[Position], key) -> list[AllocationSlice]:
    buckets: dict[str, float] = {}
    total = 0.0
    for p in positions:
        value = p.current_value if p.current_value is not None else p.cost_basis
        label = key(p) or "Inconnu"
        buckets[label] = buckets.get(label, 0.0) + value
        total += value
    slices = [
        AllocationSlice(label=label, value=value, weight_pct=(value / total * 100) if total else 0.0)
        for label, value in buckets.items()
    ]
    return sorted(slices, key=lambda s: s.value, reverse=True)


def build_allocations(positions: list[Position]):
    return (
        _allocation(positions, lambda p: p.sector),
        _allocation(positions, lambda p: p.country),
        _allocation(positions, lambda p: p.ticker),
    )


def _shares_held_over_time(transactions: list[Transaction], index: pd.DatetimeIndex) -> pd.DataFrame:
    """For each ticker, cumulative shares held at every date in `index`."""
    tickers = sorted({t.ticker for t in transactions})
    holdings = pd.DataFrame(0.0, index=index, columns=tickers)
    for tx in transactions:
        tx_date = pd.Timestamp(tx.date)
        delta = tx.quantity if tx.type.value == "BUY" else (-tx.quantity if tx.type.value == "SELL" else 0.0)
        if delta == 0.0:
            continue
        matches = holdings.index >= tx_date
        holdings.loc[matches, tx.ticker] += delta
    return holdings.clip(lower=0.0)


def build_performance_and_risk(transactions: list[Transaction]) -> tuple[list[PerformancePoint], RiskMetrics, list[str]]:
    warnings: list[str] = []
    buy_sell = [t for t in transactions if t.type.value in ("BUY", "SELL")]
    if not buy_sell:
        return [], RiskMetrics(period_days=0), warnings

    start = min(t.date for t in buy_sell)
    end = date.today()
    tickers = sorted({t.ticker for t in buy_sell})

    prices = fetch_price_history(tickers, start, end)
    if prices.empty:
        warnings.append("Historique de prix indisponible : la courbe de performance n'a pas pu être calculée.")
        return [], RiskMetrics(period_days=0), warnings

    holdings = _shares_held_over_time(buy_sell, prices.index)
    common_cols = [c for c in holdings.columns if c in prices.columns]
    if not common_cols:
        warnings.append("Aucun titre du portefeuille n'a pu être rapproché des données de marché.")
        return [], RiskMetrics(period_days=0), warnings

    portfolio_value = (holdings[common_cols] * prices[common_cols]).sum(axis=1)
    portfolio_value = portfolio_value[portfolio_value > 0]
    if portfolio_value.empty:
        return [], RiskMetrics(period_days=0), warnings

    benchmarks = fetch_benchmark_history(start, end)
    base_value = portfolio_value.iloc[0]
    portfolio_start = portfolio_value.index[0]

    benchmark_bases: dict[str, float] = {}
    for name, series in benchmarks.items():
        series_before_start = series[series.index <= portfolio_start]
        if len(series_before_start):
            benchmark_bases[name] = float(series_before_start.iloc[-1])

    points: list[PerformancePoint] = []
    for dt, value in portfolio_value.items():
        bench_returns: dict[str, float] = {}
        for name, series in benchmarks.items():
            base = benchmark_bases.get(name)
            series_aligned = series[series.index <= dt]
            if base and len(series_aligned):
                bench_returns[name] = float((series_aligned.iloc[-1] / base - 1) * 100)
        points.append(
            PerformancePoint(
                date=dt.date(),
                portfolio_value=float(value),
                portfolio_return_pct=float((value / base_value - 1) * 100),
                benchmarks_return_pct=bench_returns,
            )
        )

    daily_returns = portfolio_value.pct_change().dropna()
    risk = RiskMetrics(period_days=len(portfolio_value))
    if len(daily_returns) > 2:
        vol = daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        mean_annual_return = daily_returns.mean() * TRADING_DAYS_PER_YEAR
        drawdown = (portfolio_value / portfolio_value.cummax() - 1).min()
        risk.annualized_volatility_pct = float(vol * 100)
        risk.sharpe_ratio = float((mean_annual_return - RISK_FREE_RATE) / vol) if vol else None
        risk.max_drawdown_pct = float(drawdown * 100)

    return points, risk, warnings
