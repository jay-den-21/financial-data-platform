from fdp.storage import (
    SYSTEM_SCHEMA,
    US_SHARE_SCHEMA,
    daily_price,
    data_quality_issue,
    instrument,
    market_calendar,
    metadata,
)


def test_initial_metadata_contains_project_tables() -> None:
    assert f"{US_SHARE_SCHEMA}.instrument" in metadata.tables
    assert f"{US_SHARE_SCHEMA}.daily_price" in metadata.tables
    assert f"{US_SHARE_SCHEMA}.market_calendar" in metadata.tables
    assert f"{SYSTEM_SCHEMA}.data_quality_issue" in metadata.tables
    assert f"{SYSTEM_SCHEMA}.repair_plan" in metadata.tables


def test_instrument_keeps_standard_and_provider_symbols() -> None:
    assert instrument.schema == US_SHARE_SCHEMA
    assert "symbol" in instrument.c
    assert "provider_symbol" in instrument.c
    assert {"provider", "provider_symbol"} in [
        set(constraint.columns.keys()) for constraint in instrument.constraints
    ]


def test_daily_price_has_instrument_date_uniqueness() -> None:
    assert {"instrument_id", "trade_date"} in [
        set(constraint.columns.keys()) for constraint in daily_price.constraints
    ]


def test_market_calendar_has_market_exchange_date_uniqueness() -> None:
    assert {"market", "exchange", "calendar_date"} in [
        set(constraint.columns.keys()) for constraint in market_calendar.constraints
    ]


def test_quality_issue_records_issue_identity_and_resolution_state() -> None:
    expected_columns = {
        "issue_type",
        "severity",
        "instrument_id",
        "symbol",
        "trade_date",
        "details",
        "status",
        "resolved_at",
    }
    assert expected_columns.issubset(data_quality_issue.c.keys())

