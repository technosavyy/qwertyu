from datetime import date

from tests.support import utc
from windfc.domain.breakdown import by_delivery_day, by_london_hour
from windfc.domain.metrics import HourlyError


def error(start_hour: tuple[int, int, int, int], signed: float) -> HourlyError:
    return HourlyError(utc(*start_hour), utc(2025, 12, 31, 7, 30), 1000 + signed, 1000)


def test_groups_by_london_hour_of_day() -> None:
    result = by_london_hour(
        [error((2026, 1, 1, 5), 100), error((2026, 1, 2, 5), 300), error((2026, 7, 1, 12), 50)]
    )

    assert sorted(result) == [5, 13]  # 12:00 UTC in July is 13:00 London
    assert result[5].mae_mw == 200
    assert result[5].hours == 2


def test_groups_by_delivery_day_in_order() -> None:
    result = by_delivery_day([error((2026, 1, 2, 0), 10), error((2026, 1, 1, 0), -30)])

    assert list(result) == [date(2026, 1, 1), date(2026, 1, 2)]
    assert result[date(2026, 1, 1)].bias_mw == -30
