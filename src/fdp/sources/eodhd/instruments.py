from datetime import date
from dataclasses import dataclass
from typing import Any

SUPPORTED_ASSET_TYPES = {
    "common stock": "stock",
    "stock": "stock",
    "etf": "etf",
    "fund": "etf",
}


@dataclass(frozen=True)
class RejectedInstrumentRow:
    index: int
    reason: str
    row: dict[str, Any]


@dataclass(frozen=True)
class ParsedInstrumentRows:
    accepted: list[dict[str, Any]]
    rejected: list[RejectedInstrumentRow]


def split_provider_symbol(provider_symbol: str) -> tuple[str, str]:
    parts = provider_symbol.rsplit(".", 1)
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"invalid EODHD provider_symbol: {provider_symbol!r}")
    return parts[0], parts[1]


def parse_exchange_symbol(
    payload: dict[str, Any],
    *,
    market: str = "US",
    provider: str = "EODHD",
) -> dict[str, Any] | None:
    asset_type = _normalize_asset_type(_first_present(payload, "Type", "type"))
    if asset_type is None:
        return None

    code = _required_text(payload, "Code", "code")
    name = _required_text(payload, "Name", "name")
    currency = _required_text(payload, "Currency", "currency")
    exchange = _optional_text(payload, "Exchange", "exchange") or market
    provider_symbol = _provider_symbol_from_code(code, market)
    symbol, provider_market = split_provider_symbol(provider_symbol)

    if provider_market != market:
        raise ValueError(
            f"EODHD provider_symbol market {provider_market!r} does not match {market!r}"
        )

    delisted_date = _optional_date(payload, "DelistedDate", "delisted_date")
    return {
        "market": market,
        "symbol": symbol,
        "provider": provider,
        "provider_symbol": provider_symbol,
        "name": name,
        "exchange": exchange,
        "asset_type": asset_type,
        "currency": currency,
        "is_active": delisted_date is None,
        "listed_date": _optional_date(payload, "IPODate", "listed_date"),
        "delisted_date": delisted_date,
    }


def parse_exchange_symbol_rows(
    rows: list[dict[str, Any]],
    *,
    market: str = "US",
    provider: str = "EODHD",
) -> ParsedInstrumentRows:
    accepted: list[dict[str, Any]] = []
    rejected: list[RejectedInstrumentRow] = []

    for index, row in enumerate(rows):
        try:
            parsed = parse_exchange_symbol(row, market=market, provider=provider)
        except ValueError as exc:
            rejected.append(RejectedInstrumentRow(index=index, reason=str(exc), row=row))
            continue

        if parsed is None:
            rejected.append(
                RejectedInstrumentRow(index=index, reason="unsupported_asset_type", row=row)
            )
            continue

        if not parsed["is_active"]:
            rejected.append(RejectedInstrumentRow(index=index, reason="inactive_instrument", row=row))
            continue

        accepted.append(parsed)

    return ParsedInstrumentRows(accepted=accepted, rejected=rejected)


def _normalize_asset_type(value: Any) -> str | None:
    if value is None:
        return None
    return SUPPORTED_ASSET_TYPES.get(str(value).strip().lower())


def _provider_symbol_from_code(code: str, market: str) -> str:
    if code.endswith(f".{market}"):
        return code

    if "." in code:
        symbol, suffix = code.rsplit(".", 1)
        if symbol and suffix.isalpha() and len(suffix) > 1:
            return code

    return f"{code}.{market}"


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _required_text(payload: dict[str, Any], *keys: str) -> str:
    value = _optional_text(payload, *keys)
    if value is None:
        joined_keys = ", ".join(keys)
        raise ValueError(f"missing required EODHD field: {joined_keys}")
    return value


def _optional_text(payload: dict[str, Any], *keys: str) -> str | None:
    value = _first_present(payload, *keys)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_date(payload: dict[str, Any], *keys: str) -> date | None:
    value = _first_present(payload, *keys)
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))
