"""Pydantic models shared across the portfolio analysis API."""
from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"


class Transaction(BaseModel):
    date: date
    ticker: str
    label: str | None = None
    type: TransactionType
    quantity: float
    unit_price: float
    fees: float = 0.0
    currency: str = "XOF"


class Position(BaseModel):
    ticker: str
    label: str | None = None
    quantity: float
    average_cost: float
    cost_basis: float
    current_price: float | None = None
    current_value: float | None = None
    unrealized_gain: float | None = None
    unrealized_gain_pct: float | None = None
    weight_pct: float | None = None
    sector: str | None = None
    country: str | None = None
    currency: str | None = None
    pe_ratio: float | None = None
    market_data_available: bool = True


class PortfolioSummary(BaseModel):
    total_cost_basis: float
    total_current_value: float
    total_unrealized_gain: float
    total_unrealized_gain_pct: float
    realized_gain: float
    total_dividends: float
    total_fees: float
    positions_count: int
    as_of: date


class AllocationSlice(BaseModel):
    label: str
    value: float
    weight_pct: float


class PerformancePoint(BaseModel):
    date: date
    portfolio_value: float
    portfolio_return_pct: float
    benchmarks_return_pct: dict[str, float]


class RiskMetrics(BaseModel):
    annualized_volatility_pct: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown_pct: float | None = None
    period_days: int = 0


class AnalysisResponse(BaseModel):
    summary: PortfolioSummary
    positions: list[Position]
    allocation_by_sector: list[AllocationSlice]
    allocation_by_country: list[AllocationSlice]
    allocation_by_ticker: list[AllocationSlice]
    performance: list[PerformancePoint]
    risk: RiskMetrics
    warnings: list[str] = []
