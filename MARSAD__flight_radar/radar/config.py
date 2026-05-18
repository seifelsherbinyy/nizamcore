"""All configuration and constants — loaded once from environment, never from scattered os.getenv calls."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env relative to this file's parent (MARSAD__flight_radar/)
_MODULE_ROOT = Path(__file__).parent.parent
load_dotenv(_MODULE_ROOT / ".env")


# ── Data source ───────────────────────────────────────────────────────────────
DATA_SOURCE: str = os.getenv("DATA_SOURCE", "amadeus")
SECONDARY_SOURCE: str = os.getenv("SECONDARY_SOURCE", "kiwi")

# Amadeus API
AMADEUS_CLIENT_ID: str = os.getenv("AMADEUS_CLIENT_ID", "")
AMADEUS_CLIENT_SECRET: str = os.getenv("AMADEUS_CLIENT_SECRET", "")
AMADEUS_ENV: str = os.getenv("AMADEUS_ENV", "test")  # test | production

# Kiwi Tequila
KIWI_API_KEY: str = os.getenv("KIWI_API_KEY", "")

# ITA Matrix — gated behind explicit flag to require conscious ToS acceptance
ITA_MATRIX_ENABLED: bool = os.getenv("ITA_MATRIX_ENABLED", "false").lower() == "true"
ITA_MATRIX_URL: str = os.getenv("ITA_MATRIX_URL", "https://matrix.itasoftware.com/search")

# ── Travel window ─────────────────────────────────────────────────────────────
# Ramadan 2027 estimated end: ~2027-03-09 (±1–2 days, moon-sighting dependent)
# RADAR_WINDOW_START defaults to 2027-03-15 (conservative 6-day post-Eid buffer)
WINDOW_START: str = os.getenv("RADAR_WINDOW_START", "2027-03-15")
WINDOW_END: str = os.getenv("RADAR_WINDOW_END", "2027-09-30")

# ── Routing constraints (these are not configurable — hardcoded by design) ────
ORIGIN: str = "CAI"

USA_DESTINATIONS: list[str] = [
    "JFK", "LAX", "ORD", "ATL", "MIA",
    "SFO", "IAD", "BOS", "EWR", "DFW",
    "SEA", "LAS",
]

CABINS: list[str] = ["BUSINESS", "PREMIUM_ECONOMY"]

DURATION_MIN_NIGHTS: int = 9
DURATION_MAX_NIGHTS: int = 14
MAX_ONE_WAY_HOURS: float = 30.0

# ── Carriers ──────────────────────────────────────────────────────────────────
PRIMARY_CARRIERS: list[str] = ["AF", "BA", "LH", "MS", "EK", "QR", "DL"]
SECONDARY_CARRIERS: list[str] = ["TK", "UA", "AA", "KL", "EY"]
ALL_CARRIERS: list[str] = PRIMARY_CARRIERS + SECONDARY_CARRIERS

# ── Alert thresholds ──────────────────────────────────────────────────────────
ALERT_THRESHOLD_PCT: float = float(os.getenv("ALERT_THRESHOLD_PCT", "10"))
ALERT_THRESHOLD_BUSINESS_USD: float = float(os.getenv("ALERT_THRESHOLD_BUSINESS_USD", "200"))
ALERT_THRESHOLD_PREMIUM_ECONOMY_USD: float = float(os.getenv("ALERT_THRESHOLD_PREMIUM_ECONOMY_USD", "100"))

# ── Alert delivery ────────────────────────────────────────────────────────────
ALERT_DELIVERY: str = os.getenv("ALERT_DELIVERY", "console_and_file")
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
ALERT_WEBHOOK_URL: str = os.getenv("ALERT_WEBHOOK_URL", "")

# ── File paths ────────────────────────────────────────────────────────────────
DATA_DIR: Path = _MODULE_ROOT / os.getenv("DATA_DIR", "data")
ALERTS_DIR: Path = _MODULE_ROOT / os.getenv("ALERTS_DIR", "alerts")
BACKUPS_DIR: Path = DATA_DIR / "backups"

FLIGHT_PRICES_PATH: Path = DATA_DIR / "flight_prices.json"
FLIGHT_PRICES_TMP: Path = DATA_DIR / "flight_prices.tmp"
RADAR_ALERTS_PATH: Path = ALERTS_DIR / "radar_alerts.json"

# ── Rate limiting ─────────────────────────────────────────────────────────────
FETCH_DELAY_MIN_SEC: float = float(os.getenv("FETCH_DELAY_MIN_SEC", "3"))
FETCH_DELAY_MAX_SEC: float = float(os.getenv("FETCH_DELAY_MAX_SEC", "12"))
MAX_REQUESTS_PER_SESSION: int = int(os.getenv("MAX_REQUESTS_PER_SESSION", "50"))

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCHEDULER_HOUR: int = int(os.getenv("SCHEDULER_HOUR", "6"))
SCHEDULER_MINUTE: int = int(os.getenv("SCHEDULER_MINUTE", "0"))

# ── Forecasting ───────────────────────────────────────────────────────────────
FORECAST_LOW_CONFIDENCE_THRESHOLD: int = 7
FORECAST_MEDIUM_CONFIDENCE_THRESHOLD: int = 30
HISTORICAL_PERCENTILE_THRESHOLD: int = 20

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ── Schema version ────────────────────────────────────────────────────────────
SCHEMA_VERSION: str = "1.0"


def validate_credentials() -> list[str]:
    """Return list of missing required credentials for the configured data source."""
    missing = []
    if DATA_SOURCE == "amadeus":
        if not AMADEUS_CLIENT_ID:
            missing.append("AMADEUS_CLIENT_ID")
        if not AMADEUS_CLIENT_SECRET:
            missing.append("AMADEUS_CLIENT_SECRET")
    elif DATA_SOURCE == "kiwi":
        if not KIWI_API_KEY:
            missing.append("KIWI_API_KEY")
    elif DATA_SOURCE == "ita_matrix":
        if not ITA_MATRIX_ENABLED:
            missing.append(
                "ITA_MATRIX_ENABLED=true (requires ToS review — see README)"
            )
    return missing
