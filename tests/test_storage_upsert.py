from datetime import date
from decimal import Decimal

from sqlalchemy.dialects import mysql

from fdp.storage.upsert import build_daily_price_upsert, build_instrument_upsert


def test_instrument_upsert_uses_mysql_duplicate_key_update() -> None:
    statement = build_instrument_upsert(
        {
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
    )

    sql = str(statement.compile(dialect=mysql.dialect()))
    update_clause = sql.split("ON DUPLICATE KEY UPDATE", maxsplit=1)[1]

    assert "ON DUPLICATE KEY UPDATE" in sql
    assert "provider_symbol = VALUES(provider_symbol)" not in update_clause
    assert "updated_at = CURRENT_TIMESTAMP" in update_clause


def test_daily_price_upsert_targets_unique_price_identity() -> None:
    statement = build_daily_price_upsert(
        {
            "instrument_id": 1,
            "trade_date": date(2024, 1, 2),
            "open": Decimal("100.00"),
            "high": Decimal("101.00"),
            "low": Decimal("99.00"),
            "close": Decimal("100.50"),
            "adjusted_close": Decimal("100.45"),
            "volume": 1_000_000,
            "currency": "USD",
            "source": "EODHD",
        }
    )

    sql = str(statement.compile(dialect=mysql.dialect()))

    assert "ON DUPLICATE KEY UPDATE" in sql
    assert "adjusted_close = VALUES(adjusted_close)" in sql
    assert "volume = VALUES(volume)" in sql

