"""HTTP client for the Elexon BMRS stream endpoints.

It returns raw rows exactly as Elexon sends them; validation lives in ``parse`` so the
two concerns stay separate. Network access and sleeping are injectable, so tests never
touch the internet (ADR-014).
"""

import json
import logging
import time
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from windfc.constants import (
    ACTUALS_DATASET,
    ELEXON_BASE_URL,
    FORECASTS_DATASET,
    FUEL_TYPE_WIND,
)
from windfc.errors import ElexonError, ElexonHttpError
from windfc.timeutil import format_utc

logger = logging.getLogger(__name__)

FetchJson = Callable[[str], object]
Sleep = Callable[[float], None]
RawRow = Mapping[str, object]

_REQUEST_TIMEOUT_SECONDS = 120
_RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def urllib_fetch_json(url: str) -> object:
    """Fetch ``url`` and decode the JSON body, mapping failures to typed errors."""
    request = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            payload: object = json.load(response)
            return payload
    except HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        raise ElexonHttpError(exc.code, body) from exc
    except URLError as exc:
        raise ElexonError(f"network error: {exc.reason}") from exc


class ElexonClient:
    """Download FUELHH actuals and WINDFOR forecasts, retrying when Elexon asks us to wait."""

    def __init__(
        self,
        *,
        base_url: str = ELEXON_BASE_URL,
        fetch_json: FetchJson = urllib_fetch_json,
        sleep: Sleep = time.sleep,
        max_attempts: int = 5,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        self._base_url = base_url
        self._fetch_json = fetch_json
        self._sleep = sleep
        self._max_attempts = max_attempts

    def fetch_actual_rows(self, first_day: date, last_day: date) -> list[RawRow]:
        """Wind actuals for settlement days ``first_day`` to ``last_day``, inclusive."""
        params = {
            "settlementDateFrom": first_day.isoformat(),
            "settlementDateTo": last_day.isoformat(),
            "fuelType": FUEL_TYPE_WIND,
        }
        return self._get_rows(ACTUALS_DATASET, params)

    def fetch_forecast_rows(self, publish_from: datetime, publish_to: datetime) -> list[RawRow]:
        """Forecasts published from ``publish_from`` up to ``publish_to``, one day per call.

        Calls are made a day at a time to stay well inside any range limit. A forecast
        sitting exactly on a day boundary can be returned by two adjacent calls, so
        identical repeats are dropped.
        """
        rows: dict[tuple[object, object], RawRow] = {}
        chunk_start = publish_from
        while chunk_start < publish_to:
            chunk_end = min(chunk_start + timedelta(days=1), publish_to)
            params = {
                "publishDateTimeFrom": format_utc(chunk_start),
                "publishDateTimeTo": format_utc(chunk_end),
            }
            for row in self._get_rows(FORECASTS_DATASET, params):
                rows.setdefault((row.get("publishTime"), row.get("startTime")), row)
            chunk_start = chunk_end
        return list(rows.values())

    def _get_rows(self, dataset: str, params: Mapping[str, str]) -> list[RawRow]:
        url = f"{self._base_url}/{dataset}/stream?{urlencode(params)}"
        payload = self._fetch_with_retry(url)
        if not isinstance(payload, list):
            raise ElexonError(f"{dataset}: expected a JSON list, got {type(payload).__name__}")
        logger.info("%s %s -> %d rows", dataset, dict(params), len(payload))
        return payload

    def _fetch_with_retry(self, url: str) -> object:
        for attempt in range(self._max_attempts):
            try:
                return self._fetch_json(url)
            except ElexonHttpError as exc:
                if exc.status_code not in _RETRYABLE_STATUS_CODES:
                    raise
                failure: ElexonError = exc
            except ElexonError as exc:
                failure = exc
            if attempt + 1 == self._max_attempts:
                raise ElexonError(f"giving up after {self._max_attempts} attempts: {failure}")
            delay = float(2**attempt)
            logger.warning("%s; retrying in %.0fs", failure, delay)
            self._sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover
