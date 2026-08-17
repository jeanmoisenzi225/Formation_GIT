"""Build portfolio positions from a list of transactions using the weighted
average cost method (coût moyen pondéré), the standard approach for retail
brokerage accounts.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import Transaction, TransactionType


@dataclass
class _Lot:
    quantity: float = 0.0
    average_cost: float = 0.0
    label: str | None = None
    currency: str = "EUR"
    realized_gain: float = 0.0
    dividends: float = 0.0
    fees_paid: float = 0.0


@dataclass
class PortfolioState:
    # All tickers ever traded, including fully closed positions. Used to
    # compute portfolio-wide totals (realized gains, dividends, fees).
    all_lots: dict[str, _Lot] = field(default_factory=dict)
    # Only tickers currently held (quantity > 0). Used to render positions.
    lots: dict[str, _Lot] = field(default_factory=dict)

    @property
    def total_realized_gain(self) -> float:
        return sum(lot.realized_gain for lot in self.all_lots.values())

    @property
    def total_dividends(self) -> float:
        return sum(lot.dividends for lot in self.all_lots.values())

    @property
    def total_fees(self) -> float:
        return sum(lot.fees_paid for lot in self.all_lots.values())


def build_positions(transactions: list[Transaction]) -> PortfolioState:
    state = PortfolioState()
    ordered = sorted(transactions, key=lambda t: t.date)

    for tx in ordered:
        lot = state.all_lots.setdefault(tx.ticker, _Lot(label=tx.label, currency=tx.currency))
        if tx.label and not lot.label:
            lot.label = tx.label

        if tx.type == TransactionType.BUY:
            total_cost_before = lot.average_cost * lot.quantity
            total_cost_new = tx.unit_price * tx.quantity + tx.fees
            new_quantity = lot.quantity + tx.quantity
            lot.average_cost = (total_cost_before + total_cost_new) / new_quantity if new_quantity else 0.0
            lot.quantity = new_quantity
            lot.fees_paid += tx.fees

        elif tx.type == TransactionType.SELL:
            sell_quantity = min(tx.quantity, lot.quantity) if lot.quantity else 0.0
            realized = (tx.unit_price - lot.average_cost) * sell_quantity - tx.fees
            lot.realized_gain += realized
            lot.quantity = max(lot.quantity - sell_quantity, 0.0)
            lot.fees_paid += tx.fees
            if lot.quantity == 0:
                lot.average_cost = 0.0

        elif tx.type == TransactionType.DIVIDEND:
            lot.dividends += tx.unit_price * tx.quantity if tx.quantity else tx.unit_price

        elif tx.type == TransactionType.FEE:
            lot.fees_paid += tx.fees or tx.unit_price

    # Positions view excludes tickers fully sold out of the current portfolio.
    state.lots = {ticker: lot for ticker, lot in state.all_lots.items() if lot.quantity > 1e-9}
    return state
