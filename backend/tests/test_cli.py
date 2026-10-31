import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from tests.support import TWO_DAYS, complete_actual_rows, complete_forecast_rows
from windfc.data.loader import load_snapshot
from windfc.errors import ElexonHttpError
from windfc.ingestion.cli import RAW_ACTUALS_FILENAME, RAW_FORECASTS_FILENAME, main
from windfc.ingestion.client import ElexonClient

WINDOW_ARGS = ["--first-day", "2026-01-01", "--last-day", "2026-01-02"]


def write_raw(raw_dir: Path) -> None:
    raw_dir.mkdir()
    (raw_dir / RAW_ACTUALS_FILENAME).write_text(json.dumps(complete_actual_rows(TWO_DAYS)))
    (raw_dir / RAW_FORECASTS_FILENAME).write_text(json.dumps(complete_forecast_rows(TWO_DAYS)))


def test_build_turns_raw_files_into_a_loadable_snapshot(tmp_path: Path) -> None:
    write_raw(tmp_path / "raw")

    code = main(
        [
            "build",
            "--raw-dir",
            str(tmp_path / "raw"),
            "--out-dir",
            str(tmp_path / "out"),
            *WINDOW_ARGS,
        ]
    )

    assert code == 0
    snapshot = load_snapshot(tmp_path / "out")
    assert (len(snapshot.actuals), len(snapshot.forecasts)) == (96, 48)


def test_build_reports_a_missing_raw_file_and_fails(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    code = main(
        ["build", "--raw-dir", str(tmp_path), "--out-dir", str(tmp_path / "out"), *WINDOW_ARGS]
    )

    assert code == 1
    assert "run the fetch command first" in caplog.text


def test_build_reports_invalid_json_and_fails(tmp_path: Path) -> None:
    write_raw(tmp_path / "raw")
    (tmp_path / "raw" / RAW_ACTUALS_FILENAME).write_text("{oops")

    code = main(
        [
            "build",
            "--raw-dir",
            str(tmp_path / "raw"),
            "--out-dir",
            str(tmp_path / "out"),
            *WINDOW_ARGS,
        ]
    )

    assert code == 1


def test_build_rejects_raw_files_that_are_not_lists(tmp_path: Path) -> None:
    write_raw(tmp_path / "raw")
    (tmp_path / "raw" / RAW_FORECASTS_FILENAME).write_text('{"rows": []}')

    code = main(
        [
            "build",
            "--raw-dir",
            str(tmp_path / "raw"),
            "--out-dir",
            str(tmp_path / "out"),
            *WINDOW_ARGS,
        ]
    )

    assert code == 1


def test_fetch_saves_raw_files_and_looks_back_three_days(tmp_path: Path) -> None:
    urls: list[str] = []

    def fake_fetch(url: str) -> object:
        urls.append(url)
        if "/FUELHH/" in url:
            return complete_actual_rows(TWO_DAYS)
        return complete_forecast_rows(TWO_DAYS)

    client = ElexonClient(fetch_json=fake_fetch, sleep=lambda _: None)

    code = main(["fetch", "--raw-dir", str(tmp_path), *WINDOW_ARGS], client=client)

    assert code == 0
    assert len(json.loads((tmp_path / RAW_ACTUALS_FILENAME).read_text())) == 96
    assert len(json.loads((tmp_path / RAW_FORECASTS_FILENAME).read_text())) == 48
    forecast_calls = [parse_qs(urlparse(url).query) for url in urls if "/WINDFOR/" in url]
    assert forecast_calls[0]["publishDateTimeFrom"] == ["2025-12-29T00:00:00Z"]
    assert forecast_calls[-1]["publishDateTimeTo"] == ["2026-01-02T00:00:00Z"]


def test_fetch_fails_cleanly_when_elexon_refuses(tmp_path: Path) -> None:
    def refuse(url: str) -> object:
        raise ElexonHttpError(400, "bad parameter")

    code = main(
        ["fetch", "--raw-dir", str(tmp_path), *WINDOW_ARGS], client=ElexonClient(fetch_json=refuse)
    )

    assert code == 1


def test_rejects_unknown_commands() -> None:
    with pytest.raises(SystemExit) as caught:
        main(["bogus"])

    assert caught.value.code == 2


def test_rejects_a_reversed_window() -> None:
    with pytest.raises(SystemExit) as caught:
        main(["build", "--first-day", "2026-01-05", "--last-day", "2026-01-01"])

    assert caught.value.code == 2
