import json
from urllib.parse import parse_qs, urlparse

from fdp.sources.eodhd.client import EodhdClient


class FakeResponse:
    status = 200

    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_eodhd_client_fetches_active_exchange_symbols() -> None:
    requested_urls: list[str] = []

    def fake_transport(request, timeout: int) -> FakeResponse:
        assert timeout == 30
        requested_urls.append(request.full_url)
        return FakeResponse([{"Code": "AAPL", "Type": "Common Stock"}])

    client = EodhdClient(api_key="test-token", transport=fake_transport)
    response = client.get_exchange_symbols("US")

    parsed_url = urlparse(requested_urls[0])
    query = parse_qs(parsed_url.query)

    assert parsed_url.path == "/api/exchange-symbol-list/US"
    assert query["api_token"] == ["test-token"]
    assert query["fmt"] == ["json"]
    assert query["delisted"] == ["0"]
    assert response.success is True
    assert response.endpoint == "/exchange-symbol-list/US"
    assert response.rows_returned == 1
    assert response.payload == [{"Code": "AAPL", "Type": "Common Stock"}]

