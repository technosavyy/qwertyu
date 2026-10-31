"""HTTP contract tests. Business rules are tested in the service; this checks the wiring."""

import pytest
from fastapi.testclient import TestClient

from tests.services.fixtures import synthetic_snapshot
from windfc.api.app import create_app
from windfc.services.forecast_service import ForecastService


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(create_app(ForecastService(synthetic_snapshot())))


def test_health(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["snapshot_generated_at"] == "2026-02-01T12:00:00Z"


def test_meta(client: TestClient) -> None:
    body = client.get("/api/meta").json()

    assert body["window"] == {"first_day": "2026-01-01", "last_day": "2026-01-06"}
    assert body["default_day"] == "2026-01-06"
    assert body["default_cutoff"] == "09:00"
    assert body["confidence_options"] == [90, 95]
    assert body["publish_run_times"] == ["07:30", "09:30"]


def test_day_defaults_to_the_last_day_at_nine(client: TestClient) -> None:
    body = client.get("/api/day").json()

    assert body["delivery_day"] == "2026-01-06"
    assert body["cutoff"] == "09:00"
    assert len(body["hours"]) == 24


def test_day_returns_hand_checked_values(client: TestClient) -> None:
    body = client.get("/api/day", params={"date": "2026-01-05", "confidence": 90}).json()

    assert body["cutoff_utc"] == "2026-01-04T09:00:00Z"
    assert body["forecast_runs"] == ["2026-01-04T07:30:00Z"]
    assert body["buffer"] == {
        "confidence": 90,
        "buffer_mw": 800.0,
        "history_hours": 81,
        "enough_history": True,
    }
    assert body["hours"][0] == {
        "start_time": "2026-01-05T00:00:00Z",
        "forecast_mw": 1600.0,
        "publish_time": "2026-01-04T07:30:00Z",
        "actual_mw": 1000.0,
        "error_mw": 600.0,
        "plan_for_mw": 800.0,
    }
    assert body["metrics"]["hours"] == 24


def test_day_shows_unknowns_as_null(client: TestClient) -> None:
    body = client.get("/api/day", params={"date": "2026-01-04", "cutoff": "00:00"}).json()

    assert body["metrics"] is None
    assert body["buffer"]["buffer_mw"] is None
    assert body["hours"][0]["forecast_mw"] is None


@pytest.mark.parametrize(
    ("params", "fragment"),
    [
        ({"date": "2026-02-01"}, "between 2026-01-01 and 2026-01-06"),
        ({"confidence": 80}, "confidence"),
        ({"cutoff": "9am"}, "pattern"),
        ({"cutoff": "24:00"}, "pattern"),
        ({"date": "not-a-date"}, "date"),
    ],
)
def test_day_rejects_bad_input_with_a_clear_message(
    client: TestClient, params: dict[str, object], fragment: str
) -> None:
    response = client.get("/api/day", params=params)

    assert response.status_code == 422
    assert fragment in response.text


def test_accuracy(client: TestClient) -> None:
    body = client.get("/api/accuracy", params={"cutoff": "09:00", "confidence": 90}).json()

    assert body["overall"]["hours"] == 143
    assert [item["hour"] for item in body["by_hour"]] == list(range(24))
    assert body["by_day"][0]["day"] == "2026-01-01"
    assert body["backtest"]["hours_tested"] == 47
    assert body["backtest"]["hours_covered"] == 42


def test_accuracy_with_nothing_measurable_is_a_clear_422(client: TestClient) -> None:
    response = client.get("/api/accuracy", params={"cutoff": "00:00"})

    assert response.status_code == 422
    assert "no hours could be measured" in response.json()["detail"]


def test_revisions(client: TestClient) -> None:
    body = client.get("/api/revisions", params={"start_time": "2026-01-05T00:00:00Z"}).json()

    assert body["selected_publish_time"] == "2026-01-04T07:30:00Z"
    assert [item["available_at_cutoff"] for item in body["revisions"]] == [True, False]
    assert body["revisions"][0]["hours_ahead"] == 16.5


def test_revisions_reject_a_time_without_timezone(client: TestClient) -> None:
    response = client.get("/api/revisions", params={"start_time": "2026-01-05T00:00:00"})

    assert response.status_code == 422
    assert "timezone" in response.json()["detail"]


def test_openapi_docs_are_served(client: TestClient) -> None:
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/docs").status_code == 200


def test_production_entry_point_serves_the_committed_snapshot() -> None:
    from windfc.api.main import app

    body = TestClient(app).get("/api/day", params={"date": "2026-01-31"}).json()

    assert body["cutoff_utc"] == "2026-01-30T09:00:00Z"
    assert body["buffer"]["enough_history"] is True
