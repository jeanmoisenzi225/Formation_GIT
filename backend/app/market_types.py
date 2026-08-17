"""Shared types for market data providers (BRVM scraper, Yahoo Finance)."""
from __future__ import annotations


class TickerInfo:
    def __init__(self, current_price: float | None, sector: str | None, country: str | None,
                 currency: str | None, pe_ratio: float | None, name: str | None):
        self.current_price = current_price
        self.sector = sector
        self.country = country
        self.currency = currency
        self.pe_ratio = pe_ratio
        self.name = name
