from datetime import datetime

from tests.support import TWO_DAYS, actual_row, forecast_row, utc
from windfc.domain.evaluation import Evaluation, evaluate
from windfc.ingestion.parse import parse_actuals, parse_forecasts

DAY1_PUBLISH = utc(2025, 12, 31, 7, 30)  # before the 09:00 cutoff for 1 Jan
DAY2_PUBLISH = utc(2026, 1, 1, 7, 30)  # before the 09:00 cutoff for 2 Jan


def actual_rows(skip: set[datetime] | None = None) -> list[dict[str, object]]:
    """Half-hour k has 1000 + k MW, so hour i averages 1000 + 2i + 0.5."""
    return [
        actual_row(start, 1000 + index)
        for index, start in enumerate(TWO_DAYS.half_hours())
        if start not in (skip or set())
    ]


def forecast_rows(skip: set[datetime] | None = None) -> list[dict[str, object]]:
    """Hour i is forecast as 2000 + i, published before that day's cutoff."""
    return [
        forecast_row(DAY1_PUBLISH if index < 24 else DAY2_PUBLISH, start, 2000 + index)
        for index, start in enumerate(TWO_DAYS.hours())
        if start not in (skip or set())
    ]


def run(
    skip_forecast: set[datetime] | None = None,
    skip_actual: set[datetime] | None = None,
    extra_forecasts: list[dict[str, object]] | None = None,
) -> Evaluation:
    return evaluate(
        actuals=parse_actuals(actual_rows(skip_actual)),
        forecasts=parse_forecasts([*forecast_rows(skip_forecast), *(extra_forecasts or [])]),
        window=TWO_DAYS,
    )


def test_pairs_every_hour_and_computes_forecast_minus_actual() -> None:
    result = run()

    assert result.expected_hours == 48
    assert len(result.errors) == 48
    assert result.hours_without_forecast == ()
    assert result.hours_without_actual == ()
    # Hour 0: forecast 2000, actual (1000 + 1001) / 2 = 1000.5 -> error 999.5.
    assert result.errors[0].error_mw == 999.5
    # Hour 47: forecast 2047, actual (1094 + 1095) / 2 = 1094.5 -> error 952.5.
    assert result.errors[47].error_mw == 952.5


def test_each_day_uses_the_forecast_published_before_its_own_cutoff() -> None:
    result = run()

    assert result.errors[0].publish_time == DAY1_PUBLISH
    assert result.errors[24].publish_time == DAY2_PUBLISH


def test_a_forecast_published_after_the_cutoff_is_never_used() -> None:
    too_late = forecast_row(utc(2025, 12, 31, 9, 30), utc(2026, 1, 1, 0), 99_999)

    result = run(extra_forecasts=[too_late])

    assert result.errors[0].forecast_mw == 2000


def test_a_newer_forecast_before_the_cutoff_replaces_an_older_one() -> None:
    newer = forecast_row(utc(2025, 12, 31, 8, 30), utc(2026, 1, 1, 0), 3000)

    assert run(extra_forecasts=[newer]).errors[0].forecast_mw == 3000


def test_hours_without_a_forecast_are_listed_not_guessed() -> None:
    missing = utc(2026, 1, 2, 5)

    result = run(skip_forecast={missing})

    assert result.hours_without_forecast == (missing,)
    assert len(result.errors) == 47
    assert missing not in {item.start_time for item in result.errors}


def test_hours_with_an_incomplete_actual_are_listed_not_guessed() -> None:
    result = run(skip_actual={utc(2026, 1, 1, 3, 30)})

    assert result.hours_without_actual == (utc(2026, 1, 1, 3),)
    assert len(result.errors) == 47
