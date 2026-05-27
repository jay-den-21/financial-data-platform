from dataclasses import dataclass
from typing import Any

from fdp.sources.eodhd.client import EodhdApiResponse
from fdp.sources.eodhd.ingestion import load_exchange_symbols
from fdp.storage.tables import api_call_log, ingestion_task_run, instrument


@dataclass
class FakeResult:
    inserted_primary_key: tuple[int, ...] = ()


class FakeConnection:
    def __init__(self) -> None:
        self.statements: list[Any] = []

    def execute(self, statement) -> FakeResult:
        self.statements.append(statement)
        table = getattr(statement, "table", None)
        if table is ingestion_task_run:
            return FakeResult(inserted_primary_key=(123,))
        return FakeResult()


class FakeClient:
    def get_exchange_symbols(self, market: str) -> EodhdApiResponse:
        assert market == "US"
        return EodhdApiResponse(
            endpoint="/exchange-symbol-list/US",
            status_code=200,
            success=True,
            retry_count=0,
            rows_returned=3,
            duration_ms=12,
            payload=[
                {
                    "Code": "AAPL",
                    "Name": "Apple Inc.",
                    "Exchange": "NASDAQ",
                    "Type": "Common Stock",
                    "Currency": "USD",
                },
                {"Code": "ABC", "Type": "Bond"},
                {"Code": "BAD", "Type": "ETF", "Currency": "USD"},
            ],
        )


def test_load_exchange_symbols_records_task_api_log_and_upserts_valid_rows() -> None:
    connection = FakeConnection()

    result = load_exchange_symbols(connection, FakeClient())

    assert result == result.__class__(
        run_id=123,
        status="partial_failed",
        rows_fetched=3,
        rows_accepted=1,
        rows_rejected=2,
        api_calls=1,
        rejected_rows=result.rejected_rows,
        error_message="2 EODHD instrument row(s) were rejected",
    )
    assert [row.reason for row in result.rejected_rows] == [
        "unsupported_asset_type",
        "missing required EODHD field: Name, name",
    ]

    statement_tables = [getattr(statement, "table", None) for statement in connection.statements]
    assert statement_tables == [
        ingestion_task_run,
        api_call_log,
        instrument,
        ingestion_task_run,
    ]


class FailingClient:
    def get_exchange_symbols(self, market: str) -> EodhdApiResponse:
        return EodhdApiResponse(
            endpoint="/exchange-symbol-list/US",
            status_code=500,
            success=False,
            retry_count=3,
            rows_returned=0,
            duration_ms=30,
            payload=[],
            error_message="server error",
        )


def test_load_exchange_symbols_marks_task_failed_when_api_fails() -> None:
    connection = FakeConnection()

    result = load_exchange_symbols(connection, FailingClient())

    assert result.status == "failed"
    assert result.error_message == "server error"
    statement_tables = [getattr(statement, "table", None) for statement in connection.statements]
    assert statement_tables == [
        ingestion_task_run,
        api_call_log,
        ingestion_task_run,
    ]

