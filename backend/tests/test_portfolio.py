from datetime import date

import pytest

from app.portfolio import build_positions
from app.schemas import Transaction, TransactionType


def tx(d, ticker, type_, qty, price, fees=0.0):
    return Transaction(date=d, ticker=ticker, type=type_, quantity=qty, unit_price=price, fees=fees)


def test_weighted_average_cost():
    transactions = [
        tx(date(2023, 1, 1), "AAPL", TransactionType.BUY, 10, 100.0, fees=5.0),
        tx(date(2023, 2, 1), "AAPL", TransactionType.BUY, 10, 120.0, fees=5.0),
    ]
    state = build_positions(transactions)
    lot = state.lots["AAPL"]
    assert lot.quantity == 20
    # (10*100+5 + 10*120+5) / 20 = 2210/20 = 110.5
    assert lot.average_cost == pytest.approx(110.5)


def test_sell_realizes_gain_and_reduces_quantity():
    transactions = [
        tx(date(2023, 1, 1), "AAPL", TransactionType.BUY, 10, 100.0),
        tx(date(2023, 3, 1), "AAPL", TransactionType.SELL, 4, 150.0),
    ]
    state = build_positions(transactions)
    lot = state.lots["AAPL"]
    assert lot.quantity == 6
    assert lot.average_cost == pytest.approx(100.0)
    assert lot.realized_gain == pytest.approx((150.0 - 100.0) * 4)


def test_fully_sold_position_excluded_but_realized_gain_kept():
    transactions = [
        tx(date(2023, 1, 1), "TSLA", TransactionType.BUY, 5, 200.0),
        tx(date(2023, 6, 1), "TSLA", TransactionType.SELL, 5, 250.0),
    ]
    state = build_positions(transactions)
    assert "TSLA" not in state.lots
    assert state.total_realized_gain == pytest.approx((250.0 - 200.0) * 5)


def test_dividends_accumulate():
    transactions = [
        tx(date(2023, 1, 1), "MC.PA", TransactionType.BUY, 2, 700.0),
        tx(date(2023, 9, 1), "MC.PA", TransactionType.DIVIDEND, 2, 12.0),
    ]
    state = build_positions(transactions)
    assert state.total_dividends == pytest.approx(24.0)
