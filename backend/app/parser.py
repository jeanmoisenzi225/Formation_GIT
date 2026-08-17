"""Parsing of brokerage account statements (relevés de compte-titres) in CSV format.

Broker exports vary a lot in column naming, so instead of expecting an exact
schema we match against a set of known aliases (French + English) for each
field. Any extra columns present in the file are simply ignored.
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd

from app.schemas import Transaction, TransactionType

COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["date", "date operation", "date d'operation", "date d'opération", "trade date"],
    "ticker": ["ticker", "symbol", "code", "code isin", "isin"],
    "label": ["libelle", "libellé", "nom", "name", "designation", "désignation", "titre"],
    "type": ["type", "sens", "operation", "opération", "nature", "transaction type"],
    "quantity": ["quantite", "quantité", "quantity", "qte", "qté", "nombre de titres", "nb titres"],
    "unit_price": ["prix", "cours", "price", "prix unitaire", "cours d'execution", "cours d'exécution", "unit price"],
    "amount": ["montant", "montant net", "montant brut", "net amount", "amount", "total"],
    "fees": ["frais", "commission", "fees", "frais de courtage"],
    "currency": ["devise", "currency"],
}

TYPE_ALIASES: dict[str, TransactionType] = {
    "achat": TransactionType.BUY,
    "buy": TransactionType.BUY,
    "vente": TransactionType.SELL,
    "sell": TransactionType.SELL,
    "dividende": TransactionType.DIVIDEND,
    "dividend": TransactionType.DIVIDEND,
    "coupon": TransactionType.DIVIDEND,
    "frais": TransactionType.FEE,
    "fee": TransactionType.FEE,
    "commission": TransactionType.FEE,
}


class CsvParseError(ValueError):
    pass


def _normalize(col: str) -> str:
    return col.strip().lower().replace("_", " ")


def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    normalized = {_normalize(c): c for c in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def _map_columns(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        found = _find_column(columns, aliases)
        if found:
            mapping[field] = found
    return mapping


def _parse_date(value: str) -> datetime:
    value = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise CsvParseError(f"Date illisible: {value!r}")
    return parsed.to_pydatetime()


def _parse_number(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(" ", "").replace(" ", "")
    text = text.replace(",", ".") if text.count(",") == 1 and text.count(".") == 0 else text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        raise CsvParseError(f"Nombre illisible: {value!r}")


def _parse_type(value: str | None, quantity: float) -> TransactionType:
    if value:
        key = str(value).strip().lower()
        if key in TYPE_ALIASES:
            return TYPE_ALIASES[key]
    return TransactionType.BUY if quantity >= 0 else TransactionType.SELL


def parse_statement_csv(content: bytes) -> tuple[list[Transaction], list[str]]:
    """Parse a broker statement CSV into a list of Transactions.

    Returns (transactions, warnings). Rows that cannot be parsed are skipped
    and reported as warnings rather than aborting the whole import.
    """
    warnings: list[str] = []
    try:
        df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
    except Exception as exc:  # pragma: no cover - defensive
        raise CsvParseError(f"Impossible de lire le fichier CSV: {exc}") from exc

    if df.empty:
        raise CsvParseError("Le fichier CSV est vide.")

    mapping = _map_columns(list(df.columns))
    missing = [f for f in ("date", "ticker", "quantity") if f not in mapping]
    if missing:
        raise CsvParseError(
            "Colonnes obligatoires manquantes: "
            + ", ".join(missing)
            + ". Colonnes trouvées: "
            + ", ".join(df.columns)
        )

    transactions: list[Transaction] = []
    for idx, row in df.iterrows():
        try:
            raw_date = row[mapping["date"]]
            raw_ticker = row[mapping["ticker"]]
            if pd.isna(raw_date) or pd.isna(raw_ticker):
                continue
            ticker = str(raw_ticker).strip().upper()
            quantity = _parse_number(row[mapping["quantity"]])

            unit_price = 0.0
            if "unit_price" in mapping and not pd.isna(row[mapping["unit_price"]]):
                unit_price = _parse_number(row[mapping["unit_price"]])
            elif "amount" in mapping and not pd.isna(row[mapping["amount"]]) and quantity:
                unit_price = abs(_parse_number(row[mapping["amount"]])) / abs(quantity)

            raw_type = row[mapping["type"]] if "type" in mapping else None
            tx_type = _parse_type(raw_type, quantity)

            fees = _parse_number(row[mapping["fees"]]) if "fees" in mapping else 0.0
            currency = str(row[mapping["currency"]]).strip().upper() if "currency" in mapping and not pd.isna(row[mapping["currency"]]) else "XOF"
            label = str(row[mapping["label"]]).strip() if "label" in mapping and not pd.isna(row[mapping["label"]]) else None

            transactions.append(
                Transaction(
                    date=_parse_date(raw_date).date(),
                    ticker=ticker,
                    label=label,
                    type=tx_type,
                    quantity=abs(quantity),
                    unit_price=unit_price,
                    fees=fees,
                    currency=currency,
                )
            )
        except CsvParseError as exc:
            warnings.append(f"Ligne {idx + 2} ignorée: {exc}")
        except Exception as exc:  # pragma: no cover - defensive
            warnings.append(f"Ligne {idx + 2} ignorée: erreur inattendue ({exc})")

    if not transactions:
        raise CsvParseError("Aucune transaction valide n'a pu être extraite du fichier.")

    return transactions, warnings
