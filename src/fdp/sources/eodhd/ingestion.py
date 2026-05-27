from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.engine import Connection

from fdp.sources.eodhd.client import EodhdClient
from fdp.sources.eodhd.instruments import RejectedInstrumentRow, parse_exchange_symbol_rows
from fdp.storage.tables import api_call_log, ingestion_task_run
from fdp.storage.upsert import build_instrument_upsert


@dataclass(frozen=True)
class InstrumentLoadResult:
    run_id: int
    status: str
    rows_fetched: int
    rows_accepted: int
    rows_rejected: int
    api_calls: int
    rejected_rows: list[RejectedInstrumentRow]
    error_message: str | None = None


def load_exchange_symbols(
    connection: Connection,
    client: EodhdClient,
    *,
    market: str = "US",
) -> InstrumentLoadResult:
    run_id = _create_task_run(connection, market=market)
    response = client.get_exchange_symbols(market)
    _record_api_call(connection, run_id=run_id, response=response)

    if not response.success:
        error_message = response.error_message or "EODHD exchange symbols request failed"
        _finish_task_run(
            connection,
            run_id=run_id,
            status="failed",
            rows_fetched=0,
            rows_inserted=0,
            rows_rejected=0,
            error_message=error_message,
        )
        return InstrumentLoadResult(
            run_id=run_id,
            status="failed",
            rows_fetched=0,
            rows_accepted=0,
            rows_rejected=0,
            api_calls=1,
            rejected_rows=[],
            error_message=error_message,
        )

    parsed_rows = parse_exchange_symbol_rows(response.payload, market=market)
    if parsed_rows.accepted:
        connection.execute(build_instrument_upsert(parsed_rows.accepted))

    status, error_message = _task_status(
        rows_fetched=response.rows_returned,
        rows_accepted=len(parsed_rows.accepted),
        rows_rejected=len(parsed_rows.rejected),
    )
    _finish_task_run(
        connection,
        run_id=run_id,
        status=status,
        rows_fetched=response.rows_returned,
        rows_inserted=len(parsed_rows.accepted),
        rows_rejected=len(parsed_rows.rejected),
        error_message=error_message,
    )

    return InstrumentLoadResult(
        run_id=run_id,
        status=status,
        rows_fetched=response.rows_returned,
        rows_accepted=len(parsed_rows.accepted),
        rows_rejected=len(parsed_rows.rejected),
        api_calls=1,
        rejected_rows=parsed_rows.rejected,
        error_message=error_message,
    )


def _create_task_run(connection: Connection, *, market: str) -> int:
    result = connection.execute(
        ingestion_task_run.insert().values(
            job_name="eodhd_exchange_symbols",
            market=market,
            source="EODHD",
            target_schema="us_share",
            target_table="instrument",
            status="running",
            started_at=_now(),
        )
    )
    return int(result.inserted_primary_key[0])


def _record_api_call(connection: Connection, *, run_id: int, response) -> None:
    connection.execute(
        api_call_log.insert().values(
            run_id=run_id,
            source="EODHD",
            endpoint=response.endpoint,
            provider_symbol=None,
            status_code=response.status_code,
            success=response.success,
            retry_count=response.retry_count,
            rows_returned=response.rows_returned,
            error_message=response.error_message,
            called_at=_now(),
            duration_ms=response.duration_ms,
        )
    )


def _finish_task_run(
    connection: Connection,
    *,
    run_id: int,
    status: str,
    rows_fetched: int,
    rows_inserted: int,
    rows_rejected: int,
    error_message: str | None,
) -> None:
    connection.execute(
        update(ingestion_task_run)
        .where(ingestion_task_run.c.run_id == run_id)
        .values(
            status=status,
            finished_at=_now(),
            rows_fetched=rows_fetched,
            rows_inserted=rows_inserted,
            rows_updated=0,
            rows_rejected=rows_rejected,
            api_calls=1,
            error_message=error_message,
        )
    )


def _task_status(*, rows_fetched: int, rows_accepted: int, rows_rejected: int) -> tuple[str, str | None]:
    if rows_rejected == 0:
        return "success", None
    if rows_accepted == 0 and rows_fetched > 0:
        return "failed", "all fetched EODHD instrument rows were rejected"
    return "partial_failed", f"{rows_rejected} EODHD instrument row(s) were rejected"


def _now() -> datetime:
    return datetime.now(UTC)
