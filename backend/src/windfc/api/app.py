"""HTTP layer: validates input, calls ``ForecastService``, shapes the response (ADR-004).

No business rules live here. Everything is served under ``/api`` on the same origin as the
frontend, so there is no CORS to configure (ADR-011).
"""

import logging
from datetime import date, datetime, time
from typing import Annotated

from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.responses import JSONResponse

from windfc import __version__
from windfc.api.schemas import (
    AccuracyOut,
    BacktestOut,
    BufferOut,
    DayMetricsOut,
    DayOut,
    HealthOut,
    HourOfDayOut,
    HourOut,
    MetaOut,
    MetricsOut,
    RevisionOut,
    RevisionsOut,
    WindowOut,
)
from windfc.api.settings import snapshot_dir
from windfc.constants import DEFAULT_CUTOFF_TIME
from windfc.data.loader import load_snapshot
from windfc.errors import InvalidRequestError
from windfc.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)

_HHMM = r"^([01]\d|2[0-3]):[0-5]\d$"
Cutoff = Annotated[
    str,
    Query(pattern=_HHMM, description="Decision cutoff, London time HH:MM on the day before"),
]
Confidence = Annotated[int, Query(description="Buffer confidence level: 90 or 95")]


def format_hhmm(value: time) -> str:
    return value.strftime("%H:%M")


def parse_hhmm(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


DEFAULT_CUTOFF = format_hhmm(DEFAULT_CUTOFF_TIME)

TAGS = [
    {
        "name": "Decision",
        "description": "What the buyer could see at the cutoff, and how much to hold back.",
    },
    {"name": "Accuracy", "description": "How far past forecasts were from what actually happened."},
    {"name": "System", "description": "Liveness and configuration for the frontend."},
]


def create_app(service: ForecastService | None = None) -> FastAPI:
    """Build the application. Tests pass a service; production loads the snapshot."""
    if service is None:
        directory = snapshot_dir()
        logger.info("loading snapshot from %s", directory)
        service = ForecastService(load_snapshot(directory))

    app = FastAPI(
        title="Wind forecast decision support",
        version=__version__,
        description="Day-ahead UK wind forecasts at decision time, and how far to trust them.",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
        openapi_tags=TAGS,
    )

    @app.exception_handler(InvalidRequestError)
    async def invalid_request(_: Request, exc: InvalidRequestError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    app.include_router(_build_router(service), prefix="/api")
    return app


def _build_router(service: ForecastService) -> APIRouter:
    router = APIRouter()

    @router.get("/health", tags=["System"], summary="Is the service up, and how fresh is the data?")
    def health() -> HealthOut:
        """Returns `ok`, the API version and when the data snapshot was built."""
        meta = service.meta(DEFAULT_CUTOFF_TIME)
        return HealthOut(
            status="ok", version=__version__, snapshot_generated_at=meta.snapshot_generated_at
        )

    @router.get("/meta", tags=["System"], summary="Date range, defaults and choices for the screen")
    def meta() -> MetaOut:
        """Everything the frontend needs before its first question: the delivery days covered,
        the default day and cutoff, the buffer confidence levels on offer, and the London times
        at which forecasts are regularly published."""
        result = service.meta(DEFAULT_CUTOFF_TIME)
        return MetaOut(
            window=WindowOut.model_validate(result.window),
            default_day=result.default_day,
            default_cutoff=format_hhmm(result.default_cutoff),
            confidence_options=list(result.confidence_options),
            publish_run_times=[format_hhmm(run) for run in result.publish_run_times],
            snapshot_generated_at=result.snapshot_generated_at,
        )

    @router.get(
        "/day",
        tags=["Decision"],
        summary="The forecast available at the cutoff for one delivery day",
    )
    def day(
        delivery_day: Annotated[
            date | None, Query(alias="date", description="Delivery day, YYYY-MM-DD")
        ] = None,
        cutoff: Cutoff = DEFAULT_CUTOFF,
        confidence: Confidence = 90,
    ) -> DayOut:
        """Hour by hour: the newest forecast published at or before the cutoff, the actual wind,
        the error (forecast minus actual, positive = too high), and the level to plan for after
        the safety buffer. Unknown values are null."""
        chosen = delivery_day or service.meta(DEFAULT_CUTOFF_TIME).default_day
        view = service.day(chosen, parse_hhmm(cutoff), confidence)
        return DayOut(
            delivery_day=view.delivery_day,
            cutoff=format_hhmm(view.cutoff_time),
            cutoff_utc=view.cutoff_utc,
            forecast_runs=list(view.forecast_runs),
            hours=[HourOut.model_validate(hour) for hour in view.hours],
            buffer=BufferOut.model_validate(view.buffer),
            metrics=MetricsOut.model_validate(view.metrics) if view.metrics else None,
            hours_without_forecast=list(view.hours_without_forecast),
            hours_without_actual=list(view.hours_without_actual),
        )

    @router.get(
        "/accuracy",
        tags=["Accuracy"],
        summary="How accurate the forecast was across the whole period",
    )
    def accuracy(cutoff: Cutoff = DEFAULT_CUTOFF, confidence: Confidence = 90) -> AccuracyOut:
        """Typical miss, bias, RMSE and P90/P95 miss over every day, broken down by hour of day
        and by day, plus how often the safety buffer would really have been enough."""
        view = service.accuracy(parse_hhmm(cutoff), confidence)
        return AccuracyOut(
            cutoff=format_hhmm(view.cutoff_time),
            window=WindowOut.model_validate(view.window),
            overall=MetricsOut.model_validate(view.overall),
            by_hour=[
                HourOfDayOut(hour=hour, metrics=MetricsOut.model_validate(metrics))
                for hour, metrics in view.by_hour.items()
            ],
            by_day=[
                DayMetricsOut(day=day, metrics=MetricsOut.model_validate(metrics))
                for day, metrics in view.by_day.items()
            ],
            expected_hours=view.expected_hours,
            hours_without_forecast=list(view.hours_without_forecast),
            hours_without_actual=list(view.hours_without_actual),
            backtest=BacktestOut.model_validate(view.backtest),
        )

    @router.get(
        "/revisions",
        tags=["Accuracy"],
        summary="How the forecast for one hour changed over time",
    )
    def revisions(
        start_time: Annotated[
            datetime, Query(description="Start of the hour, ISO 8601 with timezone")
        ],
        cutoff: Cutoff = DEFAULT_CUTOFF,
    ) -> RevisionsOut:
        """Every forecast ever published for the hour, oldest first, marking which ones existed
        at the cutoff and which one the buyer would have used."""
        view = service.revisions(start_time, parse_hhmm(cutoff))
        return RevisionsOut(
            start_time=view.start_time,
            cutoff=format_hhmm(view.cutoff_time),
            cutoff_utc=view.cutoff_utc,
            revisions=[RevisionOut.model_validate(item) for item in view.revisions],
            selected_publish_time=view.selected_publish_time,
            actual_mw=view.actual_mw,
        )

    return router
