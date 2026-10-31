from datetime import date, time

import pytest

from tests.services.fixtures import HOUR_WITHOUT_ACTUAL, LATE_MW, synthetic_snapshot
from tests.support import utc
from windfc.errors import InvalidRequestError
from windfc.services.forecast_service import ForecastService

NINE = time(9, 0)


@pytest.fixture
def service() -> ForecastService:
    return ForecastService(synthetic_snapshot())


def test_meta_offers_the_window_defaults_and_regular_run_times(service: ForecastService) -> None:
    meta = service.meta(NINE)

    assert (meta.window.first_day, meta.window.last_day) == (date(2026, 1, 1), date(2026, 1, 6))
    assert meta.default_day == date(2026, 1, 6)
    assert meta.default_cutoff == NINE
    assert meta.confidence_options == (90, 95)
    assert meta.publish_run_times == (time(7, 30), time(9, 30))
    assert meta.snapshot_generated_at == utc(2026, 2, 1, 12)


def test_day_uses_the_run_before_the_cutoff_and_a_no_look_ahead_buffer(
    service: ForecastService,
) -> None:
    view = service.day(date(2026, 1, 5), NINE, 90)

    assert view.cutoff_utc == utc(2026, 1, 4, 9)
    assert view.forecast_runs == (utc(2026, 1, 4, 7, 30),)
    # History = hours finished by 4 Jan 09:00: 81 hours, errors 0..900 in a cycle.
    # Sorted, the 73rd of 81 (nearest rank for P90) is 800.
    assert view.buffer.history_hours == 81
    assert view.buffer.buffer_mw == 800
    first = view.hours[0]  # hour 96 of the window -> forecast 1600, actual 1000
    assert (first.forecast_mw, first.actual_mw, first.error_mw, first.plan_for_mw) == (
        1600,
        1000,
        600,
        800,
    )
    assert view.metrics is not None
    assert view.metrics.hours == 24
    assert view.hours_without_forecast == ()


def test_day_has_no_buffer_while_history_is_short(service: ForecastService) -> None:
    view = service.day(date(2026, 1, 4), NINE, 90)

    assert view.buffer.history_hours == 57
    assert view.buffer.buffer_mw is None
    assert all(hour.plan_for_mw is None for hour in view.hours)


def test_a_later_cutoff_picks_up_the_later_run(service: ForecastService) -> None:
    view = service.day(date(2026, 1, 5), time(10, 0), 90)

    assert {hour.forecast_mw for hour in view.hours} == {LATE_MW}


def test_day_reports_an_hour_without_an_actual(service: ForecastService) -> None:
    view = service.day(date(2026, 1, 6), NINE, 95)

    assert view.hours_without_actual == (HOUR_WITHOUT_ACTUAL,)
    gap = next(hour for hour in view.hours if hour.start_time == HOUR_WITHOUT_ACTUAL)
    assert gap.actual_mw is None
    assert gap.error_mw is None
    assert gap.forecast_mw is not None
    assert view.metrics is not None
    assert view.metrics.hours == 23


def test_day_with_no_forecast_before_the_cutoff(service: ForecastService) -> None:
    view = service.day(date(2026, 1, 2), time(0, 0), 90)

    assert len(view.hours_without_forecast) == 24
    assert view.metrics is None
    assert view.forecast_runs == ()
    assert view.hours[0].forecast_mw is None
    assert view.hours[0].plan_for_mw is None


@pytest.mark.parametrize("bad_day", [date(2025, 12, 31), date(2026, 1, 7)])
def test_day_outside_the_window_is_rejected(service: ForecastService, bad_day: date) -> None:
    with pytest.raises(InvalidRequestError, match="between 2026-01-01 and 2026-01-06"):
        service.day(bad_day, NINE, 90)


def test_unsupported_confidence_is_rejected(service: ForecastService) -> None:
    with pytest.raises(InvalidRequestError, match="confidence"):
        service.day(date(2026, 1, 5), NINE, 80)


def test_accuracy_covers_the_window_and_backtests_the_buffer(service: ForecastService) -> None:
    view = service.accuracy(NINE, 90)

    assert view.expected_hours == 144
    assert view.overall.hours == 143
    assert view.hours_without_actual == (HOUR_WITHOUT_ACTUAL,)
    assert sorted(view.by_hour) == list(range(24))
    assert len(view.by_day) == 6
    # Buffers exist from 5 Jan. Both days get 800 MW; only errors of 900 MW exceed it.
    # 5 Jan: 24 hours, three of them 900 -> 21 covered. 6 Jan: 23 measured, two 900 -> 21.
    assert (view.backtest.hours_tested, view.backtest.hours_covered) == (47, 42)


def test_accuracy_with_nothing_measurable_is_rejected(service: ForecastService) -> None:
    with pytest.raises(InvalidRequestError, match="no hours could be measured"):
        service.accuracy(time(0, 0), 90)


def test_revisions_list_every_run_and_mark_the_one_used(service: ForecastService) -> None:
    view = service.revisions(utc(2026, 1, 5), NINE)

    assert view.cutoff_utc == utc(2026, 1, 4, 9)
    assert [(r.publish_time, r.hours_ahead, r.available_at_cutoff) for r in view.revisions] == [
        (utc(2026, 1, 4, 7, 30), 16.5, True),
        (utc(2026, 1, 4, 9, 30), 14.5, False),
    ]
    assert view.selected_publish_time == utc(2026, 1, 4, 7, 30)
    assert view.actual_mw == 1000


def test_revisions_before_any_run_was_available(service: ForecastService) -> None:
    view = service.revisions(utc(2026, 1, 5), time(0, 0))

    assert view.selected_publish_time is None


@pytest.mark.parametrize(
    ("start_time", "message"),
    [
        (utc(2026, 1, 5).replace(tzinfo=None), "timezone"),
        (utc(2026, 1, 5, 0, 30), "start of an hour"),
        (utc(2026, 1, 7), "start of an hour"),
    ],
)
def test_revisions_reject_bad_start_times(
    service: ForecastService, start_time: object, message: str
) -> None:
    with pytest.raises(InvalidRequestError, match=message):
        service.revisions(start_time, NINE)  # type: ignore[arg-type]


def test_many_different_cutoffs_stay_correct_beyond_the_cache_size(
    service: ForecastService,
) -> None:
    for minute in range(70):  # 70 distinct cutoffs, 08:00 to 09:09, more than the cache holds
        service.day(date(2026, 1, 5), time(8 + minute // 60, minute % 60), 90)

    assert service.day(date(2026, 1, 5), NINE, 90).buffer.buffer_mw == 800
