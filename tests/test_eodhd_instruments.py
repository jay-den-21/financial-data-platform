from datetime import date

import pytest

from fdp.sources.eodhd import parse_exchange_symbol, parse_exchange_symbol_rows, split_provider_symbol


def test_split_provider_symbol_keeps_eodhd_symbol_and_market() -> None:
    assert split_provider_symbol("AAPL.US") == ("AAPL", "US")


def test_parse_exchange_symbol_normalizes_active_stock() -> None:
    row = parse_exchange_symbol(
        {
            "Code": "AAPL",
            "Name": "Apple Inc.",
            "Exchange": "NASDAQ",
            "Type": "Common Stock",
            "Currency": "USD",
            "IPODate": "1980-12-12",
        }
    )

    assert row == {
        "market": "US",
        "symbol": "AAPL",
        "provider": "EODHD",
        "provider_symbol": "AAPL.US",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "asset_type": "stock",
        "currency": "USD",
        "is_active": True,
        "listed_date": date(1980, 12, 12),
        "delisted_date": None,
    }


def test_parse_exchange_symbol_filters_unsupported_asset_types() -> None:
    assert parse_exchange_symbol({"Code": "ABC", "Type": "Bond"}) is None


def test_parse_exchange_symbol_rejects_market_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        parse_exchange_symbol(
            {
                "Code": "AAPL.US",
                "Name": "Apple Inc.",
                "Exchange": "NASDAQ",
                "Type": "Common Stock",
                "Currency": "USD",
            },
            market="LSE",
        )


def test_parse_exchange_symbol_rows_rejects_unsupported_malformed_and_inactive_rows() -> None:
    parsed = parse_exchange_symbol_rows(
        [
            {
                "Code": "AAPL",
                "Name": "Apple Inc.",
                "Exchange": "NASDAQ",
                "Type": "Common Stock",
                "Currency": "USD",
            },
            {"Code": "ABC", "Type": "Bond"},
            {"Code": "BAD", "Type": "ETF", "Currency": "USD"},
            {
                "Code": "OLD",
                "Name": "Old Inc.",
                "Exchange": "NYSE",
                "Type": "Common Stock",
                "Currency": "USD",
                "DelistedDate": "2020-01-01",
            },
        ]
    )

    assert [row["symbol"] for row in parsed.accepted] == ["AAPL"]
    assert [row.reason for row in parsed.rejected] == [
        "unsupported_asset_type",
        "missing required EODHD field: Name, name",
        "inactive_instrument",
    ]
