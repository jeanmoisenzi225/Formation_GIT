from datetime import date, timedelta

import pandas as pd
import pytest

from app import analytics
from app.market_data import TickerInfo
from app.portfolio import build_positions
from app.schemas import Transaction, TransactionType


def tx(d, ticker, type_, qty, price, fees=0.0):
    return Transaction(date=d, ticker=ticker, type=type_, quantity=qty, unit_price=price, fees=fees)


def test_build_positions_with_market_data(monkeypatch):
    transactions = [
        tx(date(2023, 1, 1), "ECOC", TransactionType.BUY, 10, 100.0),
        tx(date(2023, 1, 1), "SNTS", TransactionType.BUY, 2, 700.0),
    ]
    state = build_positions(transactions)

    fake_infos = {
        "ECOC": TickerInfo(current_price=150.0, sector="Services Financiers", country="Côte d'Ivoire",
                            currency="XOF", pe_ratio=None, name="Ecobank Côte d'Ivoire"),
        "SNTS": TickerInfo(current_price=750.0, sector="Télécommunications", country="Sénégal",
                            currency="XOF", pe_ratio=None, name="Sonatel"),
    }
    monkeypatch.setattr(analytics, "fetch_ticker_infos", lambda tickers: {t: fake_infos[t] for t in tickers})

    positions, warnings = analytics.build_positions_with_market_data(state)
    assert warnings == []
    by_ticker = {p.ticker: p for p in positions}

    assert by_ticker["ECOC"].current_value == pytest.approx(1500.0)
    assert by_ticker["ECOC"].unrealized_gain == pytest.approx(500.0)
    assert by_ticker["SNTS"].current_value == pytest.approx(1500.0)

    total = by_ticker["ECOC"].current_value + by_ticker["SNTS"].current_value
    assert by_ticker["ECOC"].weight_pct == pytest.approx(1500 / total * 100)


def test_build_positions_handles_missing_market_data(monkeypatch):
    transactions = [tx(date(2023, 1, 1), "UNKNOWN", TransactionType.BUY, 3, 50.0)]
    state = build_positions(transactions)
    monkeypatch.setattr(analytics, "fetch_ticker_infos", lambda tickers: {t: None for t in tickers})

    positions, warnings = analytics.build_positions_with_market_data(state)
    assert len(warnings) == 1
    assert positions[0].market_data_available is False
    assert positions[0].cost_basis == pytest.approx(150.0)


def test_allocation_by_sector():
    from app.schemas import Position

    positions = [
        Position(ticker="A", quantity=1, average_cost=10, cost_basis=10, current_value=100, sector="Tech"),
        Position(ticker="B", quantity=1, average_cost=10, cost_basis=10, current_value=300, sector="Tech"),
        Position(ticker="C", quantity=1, average_cost=10, cost_basis=10, current_value=100, sector="Health"),
    ]
    sector_alloc, _, ticker_alloc = analytics.build_allocations(positions)
    tech = next(s for s in sector_alloc if s.label == "Tech")
    assert tech.value == pytest.approx(400)
    assert tech.weight_pct == pytest.approx(80.0)
    assert len(ticker_alloc) == 3


def test_build_performance_and_risk(monkeypatch):
    start_date = date.today() - timedelta(days=30)
    transactions = [
        tx(start_date, "ECOC", TransactionType.BUY, 10, 100.0),
    ]
    dates = pd.date_range(start_date, periods=5, freq="D")
    prices = pd.DataFrame({"ECOC": [100.0, 102.0, 101.0, 105.0, 110.0]}, index=dates)
    monkeypatch.setattr(analytics, "fetch_price_history", lambda tickers, start, end: prices)
    monkeypatch.setattr(analytics, "fetch_benchmark_history", lambda start, end: {})

    points, risk, warnings = analytics.build_performance_and_risk(transactions)
    assert warnings == []
    assert len(points) == 5
    assert points[0].portfolio_return_pct == pytest.approx(0.0)
    assert points[-1].portfolio_return_pct == pytest.approx(10.0)
    assert risk.period_days == 5
