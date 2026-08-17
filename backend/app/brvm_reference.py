"""Static reference data for the BRVM (Bourse Régionale des Valeurs Mobilières),
the regional stock exchange serving the eight UEMOA/WAEMU countries.

There is no official free API for BRVM data. This module hardcodes the list
of currently listed equities (ticker -> issuing country, and the ticker
suffix used by the third-party data source `sikafinance.com` for historical
prices) so the rest of the app can work with plain BRVM tickers such as
"ECOC" or "SNTS" — the same codes used on brokerage statements.

Source: https://www.sikafinance.com (ticker directory), cross-checked
against https://www.brvm.org. New BRVM listings are rare (roughly one or two
a year) — refresh this table by hand if a ticker used in a statement isn't
recognized.
"""
from __future__ import annotations

COUNTRY_NAMES: dict[str, str] = {
    "bj": "Bénin",
    "bf": "Burkina Faso",
    "ci": "Côte d'Ivoire",
    "gw": "Guinée-Bissau",
    "ml": "Mali",
    "ne": "Niger",
    "sn": "Sénégal",
    "tg": "Togo",
}

# ticker (as it appears on BRVM statements) -> (company name, country suffix
# used by sikafinance.com, e.g. "ECOC" + "ci" -> "ECOC.ci")
TICKERS: dict[str, tuple[str, str]] = {
    "SDSC": ("Africa Global Logistics", "ci"),
    "BOAB": ("Bank of Africa Bénin", "bj"),
    "BOABF": ("Bank of Africa Burkina Faso", "bf"),
    "BOAC": ("Bank of Africa Côte d'Ivoire", "ci"),
    "BOAM": ("Bank of Africa Mali", "ml"),
    "BOAN": ("Bank of Africa Niger", "ne"),
    "BOAS": ("Bank of Africa Sénégal", "sn"),
    "BICB": ("Banque Internationale pour le Commerce du Bénin", "bj"),
    "BNBC": ("Bernabé Côte d'Ivoire", "ci"),
    "BICC": ("BICI Côte d'Ivoire", "ci"),
    "CFAC": ("CFAO Côte d'Ivoire", "ci"),
    "CIEC": ("CIE Côte d'Ivoire", "ci"),
    "CBIBF": ("Coris Bank International Burkina Faso", "bf"),
    "SEMC": ("Crown Siem", "ci"),
    "ECOC": ("Ecobank Côte d'Ivoire", "ci"),
    "SIVC": ("Erium", "ci"),
    "ETIT": ("Ecobank Transnational Incorporated", "tg"),
    "FTSC": ("Filtisac Côte d'Ivoire", "ci"),
    "LNBB": ("Loterie Nationale du Bénin", "bj"),
    "SVOC": ("Movis Côte d'Ivoire", "ci"),
    "NEIC": ("NEI-CEDA Côte d'Ivoire", "ci"),
    "NTLC": ("Nestlé Côte d'Ivoire", "ci"),
    "NSBC": ("NSIA Banque Côte d'Ivoire", "ci"),
    "ONTBF": ("Onatel Burkina Faso", "bf"),
    "ORGT": ("Oragroup Togo", "tg"),
    "ORAC": ("Orange Côte d'Ivoire", "ci"),
    "PALC": ("Palmci", "ci"),
    "SAFC": ("Safca Côte d'Ivoire", "ci"),
    "SPHC": ("Saph Côte d'Ivoire", "ci"),
    "ABJC": ("Servair Abidjan Côte d'Ivoire", "ci"),
    "STAC": ("Setao Côte d'Ivoire", "ci"),
    "SGBC": ("Société Générale Côte d'Ivoire", "ci"),
    "CABC": ("Sicable Côte d'Ivoire", "ci"),
    "SICC": ("Sicor", "ci"),
    "STBC": ("Sitab", "ci"),
    "SMBC": ("SMB Côte d'Ivoire", "ci"),
    "SIBC": ("Société Ivoirienne de Banque Côte d'Ivoire", "ci"),
    "SDCC": ("Sodeci", "ci"),
    "SOGC": ("SOGB", "ci"),
    "SLBC": ("Solibra Côte d'Ivoire", "ci"),
    "SNTS": ("Sonatel", "sn"),
    "SCRC": ("Sucrivoire", "ci"),
    "TTLC": ("Total Énergies Côte d'Ivoire", "ci"),
    "TTLS": ("Total Énergies Sénégal", "sn"),
    "PRSC": ("Tractafric Motors Côte d'Ivoire", "ci"),
    "UNLC": ("Unilever Côte d'Ivoire", "ci"),
    "UNXC": ("Uniwax Côte d'Ivoire", "ci"),
    "SHEC": ("Vivo Energy Côte d'Ivoire", "ci"),
}

# BRVM sector index pages on brvm.org — used to build a ticker -> sector map.
SECTOR_PAGES: dict[str, int] = {
    "Consommation de Base": 194,
    "Consommation Discrétionnaire": 195,
    "Énergie": 196,
    "Industriels": 197,
    "Services Financiers": 198,
    "Services Publics": 199,
    "Télécommunications": 200,
}

# Sika Finance codes for the two headline BRVM benchmarks.
BENCHMARKS: dict[str, str] = {
    "BRVM Composite": "BRVMC",
    "BRVM 30": "BRVM30",
}


def is_brvm_ticker(ticker: str) -> bool:
    return ticker.upper() in TICKERS


def sika_symbol(ticker: str) -> str | None:
    entry = TICKERS.get(ticker.upper())
    return f"{ticker.upper()}.{entry[1]}" if entry else None


def country_for(ticker: str) -> str | None:
    entry = TICKERS.get(ticker.upper())
    return COUNTRY_NAMES.get(entry[1]) if entry else None


def company_name(ticker: str) -> str | None:
    entry = TICKERS.get(ticker.upper())
    return entry[0] if entry else None
