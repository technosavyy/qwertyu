"""Response shapes. These are the public contract with the frontend: change them deliberately.

Units are in field names (``_mw``, ``_pct``). Timestamps are ISO 8601 UTC with ``Z``. Cutoff
times are London wall-clock ``HH:MM``. A null value always means "not known", never zero.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)


class WindowOut(_Model):
    first_day: date
    last_day: date


class MetricsOut(_Model):
    hours: int
    mean_actual_mw: float
    bias_mw: float
    mae_mw: float
    rmse_mw: float
    p90_abs_error_mw: float
    p95_abs_error_mw: float
    nmae_pct: float | None


class BufferOut(_Model):
    confidence: int
    buffer_mw: float | None
    history_hours: int
    enough_history: bool


class BacktestOut(_Model):
    confidence: int
    hours_tested: int
    hours_covered: int
    coverage_pct: float | None


class HealthOut(_Model):
    status: str
    version: str
    snapshot_generated_at: datetime


class MetaOut(_Model):
    window: WindowOut
    default_day: date
    default_cutoff: str
    confidence_options: list[int]
    publish_run_times: list[str]
    snapshot_generated_at: datetime


class HourOut(_Model):
    start_time: datetime
    forecast_mw: float | None
    publish_time: datetime | None
    actual_mw: float | None
    error_mw: float | None
    plan_for_mw: float | None


class DayOut(_Model):
    delivery_day: date
    cutoff: str
    cutoff_utc: datetime
    forecast_runs: list[datetime]
    hours: list[HourOut]
    buffer: BufferOut
    metrics: MetricsOut | None
    hours_without_forecast: list[datetime]
    hours_without_actual: list[datetime]


class HourOfDayOut(_Model):
    hour: int
    metrics: MetricsOut


class DayMetricsOut(_Model):
    day: date
    metrics: MetricsOut


class AccuracyOut(_Model):
    cutoff: str
    window: WindowOut
    overall: MetricsOut
    by_hour: list[HourOfDayOut]
    by_day: list[DayMetricsOut]
    expected_hours: int
    hours_without_forecast: list[datetime]
    hours_without_actual: list[datetime]
    backtest: BacktestOut


class RevisionOut(_Model):
    publish_time: datetime
    generation_mw: float
    hours_ahead: float
    available_at_cutoff: bool


class RevisionsOut(_Model):
    start_time: datetime
    cutoff: str
    cutoff_utc: datetime
    revisions: list[RevisionOut]
    selected_publish_time: datetime | None
    actual_mw: float | None
