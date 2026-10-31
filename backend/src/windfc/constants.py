"""Project-wide constants. Values come from the brief and the data spike (ADR-003)."""

from datetime import date, time, timedelta
from zoneinfo import ZoneInfo

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
ACTUALS_DATASET = "FUELHH"
FORECASTS_DATASET = "WINDFOR"
FUEL_TYPE_WIND = "WIND"

# The pilot covers purchase decisions made in January 2026, so delivery days 1 to 31 January.
PILOT_FIRST_DAY = date(2026, 1, 1)
PILOT_LAST_DAY = date(2026, 1, 31)

# The longest forecast horizon seen in the data is 66.5 hours (ADR-003). Fetching forecasts
# published up to three days before the first delivery day covers it.
FORECAST_LOOKBACK = timedelta(days=3)

# Buyers decide on the day before delivery. The default cutoff is an assumption to confirm with
# the client (ADR-001); it is a London local time, converted to UTC explicitly (ADR-008).
LONDON = ZoneInfo("Europe/London")
DEFAULT_CUTOFF_TIME = time(9, 0)
