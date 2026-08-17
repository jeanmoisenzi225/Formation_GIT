from app.brvm_reference import country_for, is_brvm_ticker, sika_symbol
from app.market_data_brvm import _parse_fr_number


def test_is_brvm_ticker():
    assert is_brvm_ticker("ECOC") is True
    assert is_brvm_ticker("ecoc") is True
    assert is_brvm_ticker("AAPL") is False


def test_sika_symbol_appends_country_suffix():
    assert sika_symbol("ECOC") == "ECOC.ci"
    assert sika_symbol("SNTS") == "SNTS.sn"
    assert sika_symbol("BOABF") == "BOABF.bf"
    assert sika_symbol("AAPL") is None


def test_country_for():
    assert country_for("SNTS") == "Sénégal"
    assert country_for("ECOC") == "Côte d'Ivoire"
    assert country_for("AAPL") is None


def test_parse_fr_number():
    assert _parse_fr_number("5\xa0731") == 5731.0
    assert _parse_fr_number("4,10") == 4.10
    assert _parse_fr_number("-0,75") == -0.75
    assert _parse_fr_number("-") is None
    assert _parse_fr_number(None) is None
