from pathlib import Path

import pytest

from app.parser import CsvParseError, parse_statement_csv
from app.schemas import TransactionType

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "releve_exemple.csv"


def test_parse_sample_statement():
    content = SAMPLE_CSV.read_bytes()
    transactions, warnings = parse_statement_csv(content)

    assert warnings == []
    assert len(transactions) == 10

    first = transactions[0]
    assert first.ticker == "ECOC"
    assert first.type == TransactionType.BUY
    assert first.quantity == 50
    assert first.unit_price == pytest.approx(6800)
    assert first.fees == pytest.approx(2500)
    assert first.currency == "XOF"

    dividend = [t for t in transactions if t.type == TransactionType.DIVIDEND][0]
    assert dividend.ticker in {"SNTS", "SDCC"}


def test_parse_english_headers():
    csv_bytes = (
        b"date,ticker,type,quantity,price,fees,currency\n"
        b"2024-01-05,MSFT,buy,4,370.5,1.5,USD\n"
        b"2024-02-10,MSFT,sell,1,400.0,1.5,USD\n"
    )
    transactions, warnings = parse_statement_csv(csv_bytes)
    assert warnings == []
    assert len(transactions) == 2
    assert transactions[0].type == TransactionType.BUY
    assert transactions[1].type == TransactionType.SELL


def test_missing_required_columns_raises():
    csv_bytes = b"foo,bar\n1,2\n"
    with pytest.raises(CsvParseError):
        parse_statement_csv(csv_bytes)


def test_empty_csv_raises():
    with pytest.raises(CsvParseError):
        parse_statement_csv(b"")


def test_amount_fallback_computes_unit_price():
    csv_bytes = (
        b"date,ticker,type,quantity,amount\n"
        b"2024-01-05,VTI,buy,2,500\n"
    )
    transactions, _ = parse_statement_csv(csv_bytes)
    assert transactions[0].unit_price == pytest.approx(250.0)
