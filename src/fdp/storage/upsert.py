from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import Table
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql import func
from sqlalchemy.sql.dml import Insert

from fdp.storage.tables import daily_price, instrument

Row = Mapping[str, Any]

'''
实现逻辑eg
INSERT INTO us_share.instrument (
  symbol,
  provider_symbol,
  name
)
VALUES (
  'AAPL',
  'AAPL.US',
  'Apple Inc.'
)
ON DUPLICATE KEY UPDATE
  symbol = VALUES(symbol),
  name = VALUES(name),
  updated_at = CURRENT_TIMESTAMP
    '''

def build_mysql_upsert(
    table: Table,
    rows: Row | Sequence[Row],
    *,
    update_columns: Sequence[str] | None = None,
) -> Insert:
    """Build a MySQL INSERT ... ON DUPLICATE KEY UPDATE statement."""
    if not rows:
        raise ValueError("rows must not be empty")

    row_keys = set(rows.keys()) if isinstance(rows, Mapping) else set(rows[0].keys())
    if update_columns is None:
        update_columns = [
            column.name
            for column in table.columns
            if not column.primary_key and column.name in row_keys and column.name != "created_at"
        ]

    statement = insert(table).values(rows)
    update_values = {}
    for column_name in update_columns:
        if column_name == "updated_at" and column_name not in row_keys:
            update_values[column_name] = func.current_timestamp()
            continue
        update_values[column_name] = getattr(statement.inserted, column_name)
    return statement.on_duplicate_key_update(**update_values)


def build_instrument_upsert(rows: Row | Sequence[Row]) -> Insert:
    return build_mysql_upsert(
        instrument,
        rows,
        update_columns=[
            "market",
            "symbol",
            "name",
            "exchange",
            "asset_type",
            "currency",
            "is_active",
            "listed_date",
            "delisted_date",
            "updated_at",
        ],
    )


def build_daily_price_upsert(rows: Row | Sequence[Row]) -> Insert:
    return build_mysql_upsert(
        daily_price,
        rows,
        update_columns=[
            "open",
            "high",
            "low",
            "close",
            "adjusted_close",
            "volume",
            "currency",
            "source",
            "source_updated_at",
            "updated_at",
        ],
    )
