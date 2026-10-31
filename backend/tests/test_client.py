import io
from email.message import Message
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

import pytest

from tests.support import utc
from windfc.errors import ElexonError, ElexonHttpError
from windfc.ingestion import client as client_module
from windfc.ingestion.client import ElexonClient, urllib_fetch_json


class FakeFetch:
    """Replays queued responses (or raises queued exceptions) and records every URL."""

    def __init__(self, *responses: object) -> None:
        self._responses = list(responses)
        self.urls: list[str] = []

    def __call__(self, url: str) -> object:
        self.urls.append(url)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def query_of(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def make_client(
    fetch: FakeFetch, sleeps: list[float] | None = None, attempts: int = 5
) -> ElexonClient:
    recorded = sleeps if sleeps is not None else []
    return ElexonClient(fetch_json=fetch, sleep=recorded.append, max_attempts=attempts)


def test_fetch_actual_rows_asks_for_wind_between_the_days() -> None:
    fetch = FakeFetch([{"generation": 1}])

    rows = make_client(fetch).fetch_actual_rows(utc(2026, 1, 1).date(), utc(2026, 1, 31).date())

    assert rows == [{"generation": 1}]
    assert urlparse(fetch.urls[0]).path.endswith("/FUELHH/stream")
    assert query_of(fetch.urls[0]) == {
        "settlementDateFrom": ["2026-01-01"],
        "settlementDateTo": ["2026-01-31"],
        "fuelType": ["WIND"],
    }


def test_fetch_forecast_rows_calls_once_per_day() -> None:
    fetch = FakeFetch([], [], [], [])

    make_client(fetch).fetch_forecast_rows(utc(2025, 12, 29), utc(2026, 1, 1, 12))

    windows = [
        (query_of(url)["publishDateTimeFrom"][0], query_of(url)["publishDateTimeTo"][0])
        for url in fetch.urls
    ]
    assert windows == [
        ("2025-12-29T00:00:00Z", "2025-12-30T00:00:00Z"),
        ("2025-12-30T00:00:00Z", "2025-12-31T00:00:00Z"),
        ("2025-12-31T00:00:00Z", "2026-01-01T00:00:00Z"),
        ("2026-01-01T00:00:00Z", "2026-01-01T12:00:00Z"),
    ]
    assert urlparse(fetch.urls[0]).path.endswith("/WINDFOR/stream")


def test_fetch_forecast_rows_drops_repeats_from_adjacent_days() -> None:
    boundary = {
        "publishTime": "2025-12-30T00:00:00Z",
        "startTime": "2025-12-30T01:00:00Z",
        "generation": 7,
    }
    other = {
        "publishTime": "2025-12-29T22:30:00Z",
        "startTime": "2025-12-30T01:00:00Z",
        "generation": 5,
    }
    fetch = FakeFetch([other, boundary], [boundary])

    rows = make_client(fetch).fetch_forecast_rows(utc(2025, 12, 29), utc(2025, 12, 31))

    assert rows == [other, boundary]


def test_retries_rate_limits_and_server_errors_with_growing_waits() -> None:
    fetch = FakeFetch(ElexonHttpError(429, "slow down"), ElexonHttpError(503, "busy"), [{"a": 1}])
    sleeps: list[float] = []

    rows = make_client(fetch, sleeps).fetch_actual_rows(
        utc(2026, 1, 1).date(), utc(2026, 1, 1).date()
    )

    assert rows == [{"a": 1}]
    assert sleeps == [1.0, 2.0]
    assert len(fetch.urls) == 3


def test_retries_network_errors() -> None:
    fetch = FakeFetch(ElexonError("network error: timed out"), [])
    sleeps: list[float] = []

    make_client(fetch, sleeps).fetch_actual_rows(utc(2026, 1, 1).date(), utc(2026, 1, 1).date())

    assert sleeps == [1.0]


def test_gives_up_after_max_attempts_without_a_final_sleep() -> None:
    fetch = FakeFetch(*[ElexonHttpError(429, "slow down")] * 3)
    sleeps: list[float] = []

    with pytest.raises(ElexonError, match="giving up after 3 attempts"):
        make_client(fetch, sleeps, attempts=3).fetch_actual_rows(
            utc(2026, 1, 1).date(), utc(2026, 1, 1).date()
        )

    assert sleeps == [1.0, 2.0]


def test_does_not_retry_client_errors() -> None:
    fetch = FakeFetch(ElexonHttpError(400, "bad parameter"))
    sleeps: list[float] = []

    with pytest.raises(ElexonHttpError) as caught:
        make_client(fetch, sleeps).fetch_actual_rows(utc(2026, 1, 1).date(), utc(2026, 1, 1).date())

    assert caught.value.status_code == 400
    assert sleeps == []
    assert len(fetch.urls) == 1


def test_rejects_responses_that_are_not_lists() -> None:
    fetch = FakeFetch({"error": "nope"})

    with pytest.raises(ElexonError, match="expected a JSON list"):
        make_client(fetch).fetch_actual_rows(utc(2026, 1, 1).date(), utc(2026, 1, 1).date())


def test_requires_at_least_one_attempt() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        ElexonClient(max_attempts=0)


def test_urllib_fetch_json_decodes_the_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        client_module, "urlopen", lambda request, timeout: io.BytesIO(b'[{"a": 1}]')
    )

    assert urllib_fetch_json("https://example.test/x") == [{"a": 1}]


def test_urllib_fetch_json_maps_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(request: object, timeout: float) -> object:
        raise HTTPError(
            "https://example.test/x", 429, "Too Many", Message(), io.BytesIO(b"slow down")
        )

    monkeypatch.setattr(client_module, "urlopen", refuse)

    with pytest.raises(ElexonHttpError) as caught:
        urllib_fetch_json("https://example.test/x")

    assert caught.value.status_code == 429
    assert "slow down" in str(caught.value)


def test_urllib_fetch_json_maps_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def unreachable(request: object, timeout: float) -> object:
        raise URLError("no route")

    monkeypatch.setattr(client_module, "urlopen", unreachable)

    with pytest.raises(ElexonError, match="no route"):
        urllib_fetch_json("https://example.test/x")
