from tests.support import utc
from windfc.domain.alignment import hourly_actuals
from windfc.models import ActualPoint


def test_an_hour_is_the_mean_of_its_two_half_hours() -> None:
    points = [ActualPoint(utc(2026, 1, 1, 0, 0), 100), ActualPoint(utc(2026, 1, 1, 0, 30), 200)]

    assert hourly_actuals(points) == {utc(2026, 1, 1, 0): 150}


def test_an_hour_with_only_its_first_half_hour_is_left_out() -> None:
    assert hourly_actuals([ActualPoint(utc(2026, 1, 1, 0, 0), 100)]) == {}


def test_an_hour_with_only_its_second_half_hour_is_left_out() -> None:
    assert hourly_actuals([ActualPoint(utc(2026, 1, 1, 0, 30), 100)]) == {}


def test_consecutive_hours_are_paired_independently_of_order() -> None:
    points = [
        ActualPoint(utc(2026, 1, 1, 1, 30), 40),
        ActualPoint(utc(2026, 1, 1, 0, 0), 10),
        ActualPoint(utc(2026, 1, 1, 1, 0), 20),
        ActualPoint(utc(2026, 1, 1, 0, 30), 30),
    ]

    assert hourly_actuals(points) == {utc(2026, 1, 1, 0): 20, utc(2026, 1, 1, 1): 30}
