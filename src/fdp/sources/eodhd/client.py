from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

Transport = Callable[..., Any]


@dataclass(frozen=True)
class EodhdApiResponse:
    endpoint: str
    status_code: int | None
    success: bool
    retry_count: int
    rows_returned: int
    duration_ms: int
    payload: list[dict[str, Any]]
    error_message: str | None = None


class EodhdClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://eodhd.com/api",
        max_retries: int = 3,
        timeout_seconds: int = 30,
        transport: Transport = urlopen,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.transport = transport

    def get_exchange_symbols(self, market: str) -> EodhdApiResponse:
        endpoint = f"/exchange-symbol-list/{market}"
        query = urlencode(
            {
                "api_token": self.api_key,
                "fmt": "json",
                "delisted": "0",
            }
        )
        url = f"{self.base_url}{endpoint}?{query}"

        started = perf_counter()
        retry_count = 0
        last_status_code: int | None = None
        last_error: str | None = None

        for attempt in range(self.max_retries + 1):
            retry_count = attempt
            try:
                request = Request(url, headers={"Accept": "application/json"})
                with self.transport(request, timeout=self.timeout_seconds) as response:
                    status_code = _response_status_code(response)
                    last_status_code = status_code
                    body = response.read().decode("utf-8")

                payload = json.loads(body)
                if not isinstance(payload, list):
                    raise ValueError("EODHD exchange symbol response must be a JSON list")

                rows = [_require_object_row(row) for row in payload]
                return EodhdApiResponse(
                    endpoint=endpoint,
                    status_code=status_code,
                    success=200 <= status_code < 300,
                    retry_count=retry_count,
                    rows_returned=len(rows),
                    duration_ms=_duration_ms(started),
                    payload=rows if 200 <= status_code < 300 else [],
                    error_message=None if 200 <= status_code < 300 else body[:1000],
                )
            except HTTPError as exc:
                last_status_code = exc.code
                last_error = str(exc)
                if exc.code < 500 or attempt >= self.max_retries:
                    break
            except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = str(exc)
                if attempt >= self.max_retries:
                    break

        return EodhdApiResponse(
            endpoint=endpoint,
            status_code=last_status_code,
            success=False,
            retry_count=retry_count,
            rows_returned=0,
            duration_ms=_duration_ms(started),
            payload=[],
            error_message=last_error,
        )


def _response_status_code(response: Any) -> int:
    status_code = getattr(response, "status", None)
    if status_code is not None:
        return int(status_code)
    return int(response.getcode())


def _require_object_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError("EODHD exchange symbol rows must be JSON objects")
    return row


def _duration_ms(started: float) -> int:
    return round((perf_counter() - started) * 1000)

