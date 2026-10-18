"""HTTP API for the current civil time in a country."""

from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from country_zones import COUNTRIES, CountryRecord

# Common names that are not the ISO 3166 short name.
ALIASES: dict[str, str] = {
    "UK": "GB",
    "U.K.": "GB",
    "Britain": "GB",
    "Great Britain": "GB",
    "United Kingdom": "GB",
    "United States": "US",
    "UAE": "AE",
    "Russia": "RU",
    "South Korea": "KR",
    "North Korea": "KP",
    "Vietnam": "VN",
    "Czech Republic": "CZ",
    "Ivory Coast": "CI",
    "Cape Verde": "CV",
    "Swaziland": "SZ",
    "Macedonia": "MK",
    "East Timor": "TL",
    "Holland": "NL",
    "The Netherlands": "NL",
    "Burma": "MM",
    "Laos": "LA",
    "Syria": "SY",
    "Turkey": "TR",
    "Vatican": "VA",
    "Vatican City": "VA",
    "DRC": "CD",
    "DR Congo": "CD",
    "Congo Kinshasa": "CD",
    "Congo Brazzaville": "CG",
    "Republic of the Congo": "CG",
}


class TimezoneClock(BaseModel):
    """Current civil time in one IANA time zone."""

    timezone: str
    region: str = Field(description="IANA note for this zone. Empty when the country has one zone.")
    local_time: str
    utc_offset: str
    abbreviation: str


class CountryTimeResponse(BaseModel):
    """Current civil time for every time zone in a country."""

    country: str
    country_code: str
    timezones: list[TimezoneClock]


class ErrorResponse(BaseModel):
    """Error body when the country cannot be resolved."""

    error: str


class HealthResponse(BaseModel):
    """Liveness or readiness status."""

    status: str


class RootResponse(BaseModel):
    """How to ask for a country's current time."""

    description: str
    sample_path: str


app = FastAPI(
    title="Country time API",
    version="0.1.0",
    description="Current civil time for a country, in each of its time zones.",
)


def normalize_country_query(value: str) -> str:
    """Fold a country name or code to a lookup key.

    Example:
        >>> normalize_country_query("  Côte d'Ivoire ")
        'cote d ivoire'
    """
    folded = unicodedata.normalize("NFKD", value.strip().casefold())
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    folded = folded.replace("&", " and ").replace(".", "")
    folded = re.sub(r"[^a-z0-9]+", " ", folded)
    return " ".join(folded.split())


def _bind(index: dict[str, str], key: str, code: str) -> None:
    """Map one lookup key to a country code, rejecting conflicting names."""
    if not key:
        return
    current = index.get(key)
    if current is not None and current != code:
        raise RuntimeError(f"country name {key!r} maps to both {current} and {code}")
    index[key] = code


def country_index() -> dict[str, str]:
    """Map normalized names and codes to ISO alpha-2 codes."""
    index: dict[str, str] = {}
    short_names: dict[str, str] = {}
    short_conflicts: set[str] = set()
    for record in COUNTRIES.values():
        _bind(index, record.code.casefold(), record.code)
        _bind(index, record.alpha3.casefold(), record.code)
        _bind(index, normalize_country_query(record.name), record.code)
        if "," not in record.name:
            continue
        head, tail = record.name.split(",", 1)
        _bind(index, normalize_country_query(f"{tail} {head}"), record.code)
        short = normalize_country_query(head)
        previous = short_names.get(short)
        if previous is not None and previous != record.code:
            short_conflicts.add(short)
        else:
            short_names[short] = record.code
    for short, code in short_names.items():
        if short in short_conflicts:
            continue
        current = index.get(short)
        if current is not None and current != code:
            continue
        _bind(index, short, code)
    for alias, code in ALIASES.items():
        if code not in COUNTRIES:
            raise RuntimeError(f"alias {alias!r} points at unknown country {code}")
        _bind(index, normalize_country_query(alias), code)
    return index


COUNTRY_INDEX = country_index()


class UnknownCountryError(LookupError):
    """The query is not a known country name or ISO code."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__(query)


def resolve_country(country: str) -> CountryRecord:
    """Return the country record for a name or ISO code."""
    shown = country.strip()
    code = COUNTRY_INDEX.get(normalize_country_query(shown))
    if code is None:
        raise UnknownCountryError(shown)
    return COUNTRIES[code]


def format_utc_offset(offset: timedelta | None) -> str:
    """Format a UTC offset as ``+HH:MM`` or ``-HH:MM``."""
    if offset is None:
        return "+00:00"
    total_seconds = int(offset.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    seconds = abs(total_seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes = remainder // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def current_country_time(country: str, now: datetime | None = None) -> CountryTimeResponse:
    """Return the current civil time in each of *country*'s time zones.

    *now* must be timezone-aware when it is supplied. The default is the current UTC time.
    """
    record = resolve_country(country)
    instant = datetime.now(UTC) if now is None else now
    if instant.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    clocks: list[TimezoneClock] = []
    seen: set[str] = set()
    for zone_name, region in record.zones:
        if zone_name in seen:
            continue
        seen.add(zone_name)
        local = instant.astimezone(ZoneInfo(zone_name))
        abbreviation = local.tzname() or ""
        clocks.append(
            TimezoneClock(
                timezone=zone_name,
                region=region,
                local_time=local.isoformat(timespec="seconds"),
                utc_offset=format_utc_offset(local.utcoffset()),
                abbreviation=abbreviation,
            )
        )
    return CountryTimeResponse(
        country=record.name,
        country_code=record.code,
        timezones=clocks,
    )


@app.get("/", response_model=RootResponse, tags=["time"])
def root() -> RootResponse:
    """Describe the country-time query."""
    return RootResponse(
        description="Current civil time for a country, in each of its time zones.",
        sample_path="/time?country=Japan",
    )


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Report that the process is running."""
    return HealthResponse(status="ok")


@app.get("/ready", response_model=HealthResponse, tags=["health"])
def ready() -> HealthResponse:
    """Report that the API can serve requests."""
    return HealthResponse(status="ready")


@app.get(
    "/time",
    response_model=CountryTimeResponse,
    responses={404: {"model": ErrorResponse}},
    tags=["time"],
)
def country_time(
    country: Annotated[
        str,
        Query(
            min_length=1,
            max_length=100,
            description="English country name or ISO 3166 code, for example Japan or JP.",
            examples=["Japan"],
        ),
    ],
) -> CountryTimeResponse | JSONResponse:
    """Return the current time in each time zone of a country."""
    if not country.strip():
        raise HTTPException(status_code=422, detail="country must not be empty")
    try:
        return current_country_time(country)
    except UnknownCountryError as exc:
        body = ErrorResponse(
            error=(
                f"Unknown country '{exc.query}'. "
                "Use an English country name or an ISO code such as JP."
            )
        )
        return JSONResponse(status_code=404, content=body.model_dump())


def main() -> None:
    """Run the API on localhost port 8001."""
    import uvicorn

    uvicorn.run("country_time_api:app", host="127.0.0.1", port=8001)


if __name__ == "__main__":
    main()
