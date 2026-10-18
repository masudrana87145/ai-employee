"""Tests for the country-time API."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from country_time_api import app, current_country_time, resolve_country
from country_zones import COUNTRIES

client = TestClient(app)

WINTER = datetime(2026, 1, 15, 15, 30, tzinfo=UTC)
SUMMER = datetime(2026, 7, 15, 15, 30, tzinfo=UTC)


class TestResolveCountry(unittest.TestCase):
    def test_english_name_and_codes(self) -> None:
        self.assertEqual(resolve_country("Japan").code, "JP")
        self.assertEqual(resolve_country("jp").code, "JP")
        self.assertEqual(resolve_country("JPN").code, "JP")

    def test_strips_whitespace_and_case(self) -> None:
        self.assertEqual(resolve_country("  japan  ").code, "JP")

    def test_accented_name(self) -> None:
        self.assertEqual(resolve_country("Côte d'Ivoire").code, "CI")
        self.assertEqual(resolve_country("cote d'ivoire").code, "CI")

    def test_common_aliases(self) -> None:
        cases = {
            "USA": "US",
            "U.S.A.": "US",
            "United States": "US",
            "UK": "GB",
            "U.K.": "GB",
            "Britain": "GB",
            "United Kingdom": "GB",
            "Russia": "RU",
            "UAE": "AE",
            "South Korea": "KR",
            "North Korea": "KP",
            "Vietnam": "VN",
            "Czech Republic": "CZ",
            "Ivory Coast": "CI",
            "Turkey": "TR",
            "Holland": "NL",
            "The Netherlands": "NL",
        }
        for name, code in cases.items():
            with self.subTest(name=name):
                self.assertEqual(resolve_country(name).code, code)

    def test_similar_names_stay_distinct(self) -> None:
        self.assertEqual(resolve_country("Guinea").code, "GN")
        self.assertEqual(resolve_country("Papua New Guinea").code, "PG")
        self.assertEqual(resolve_country("Equatorial Guinea").code, "GQ")
        self.assertEqual(resolve_country("Guinea-Bissau").code, "GW")
        self.assertEqual(resolve_country("Niger").code, "NE")
        self.assertEqual(resolve_country("Nigeria").code, "NG")
        self.assertEqual(resolve_country("Congo").code, "CG")
        self.assertEqual(resolve_country("Democratic Republic of the Congo").code, "CD")
        self.assertEqual(resolve_country("DRC").code, "CD")

    def test_bare_korea_is_not_guessed(self) -> None:
        with self.assertRaises(LookupError):
            resolve_country("Korea")

    def test_unknown_country(self) -> None:
        with self.assertRaises(LookupError):
            resolve_country("Narnia")

    def test_every_zone_loads(self) -> None:
        self.assertGreaterEqual(len(COUNTRIES), 240)
        for record in COUNTRIES.values():
            self.assertGreaterEqual(len(record.zones), 1)
            for zone_name, _region in record.zones:
                ZoneInfo(zone_name)


class TestCurrentCountryTime(unittest.TestCase):
    def test_japan_winter(self) -> None:
        result = current_country_time("Japan", now=WINTER)

        self.assertEqual(result.country, "Japan")
        self.assertEqual(result.country_code, "JP")
        self.assertEqual(len(result.timezones), 1)
        clock = result.timezones[0]
        self.assertEqual(clock.timezone, "Asia/Tokyo")
        self.assertEqual(clock.region, "")
        self.assertEqual(clock.local_time, "2026-01-16T00:30:00+09:00")
        self.assertEqual(clock.utc_offset, "+09:00")
        self.assertEqual(clock.abbreviation, "JST")

    def test_nepal_offset(self) -> None:
        clock = current_country_time("Nepal", now=WINTER).timezones[0]

        self.assertEqual(clock.timezone, "Asia/Kathmandu")
        self.assertEqual(clock.local_time, "2026-01-15T21:15:00+05:45")
        self.assertEqual(clock.utc_offset, "+05:45")

    def test_united_states_has_distinct_coasts(self) -> None:
        zones = {
            clock.timezone: clock
            for clock in current_country_time("United States", now=WINTER).timezones
        }

        self.assertEqual(zones["America/New_York"].local_time, "2026-01-15T10:30:00-05:00")
        self.assertEqual(zones["America/New_York"].region, "Eastern (most areas)")
        self.assertEqual(zones["America/Los_Angeles"].local_time, "2026-01-15T07:30:00-08:00")
        self.assertIn("Pacific/Honolulu", zones)

    def test_daylight_time(self) -> None:
        zones = {
            clock.timezone: clock for clock in current_country_time("US", now=SUMMER).timezones
        }

        self.assertEqual(zones["America/New_York"].utc_offset, "-04:00")
        self.assertEqual(zones["America/New_York"].abbreviation, "EDT")
        self.assertEqual(zones["America/New_York"].local_time, "2026-07-15T11:30:00-04:00")
        london = current_country_time("UK", now=SUMMER).timezones[0]
        self.assertEqual(london.local_time, "2026-07-15T16:30:00+01:00")
        self.assertEqual(london.abbreviation, "BST")

    def test_london_in_winter_is_utc(self) -> None:
        london = current_country_time("United Kingdom", now=WINTER).timezones[0]

        self.assertEqual(london.timezone, "Europe/London")
        self.assertEqual(london.local_time, "2026-01-15T15:30:00+00:00")
        self.assertEqual(london.abbreviation, "GMT")

    def test_rejects_naive_clock(self) -> None:
        with self.assertRaises(ValueError):
            current_country_time("Japan", now=datetime(2026, 1, 15, 15, 30))


class TestTimeEndpoint(unittest.TestCase):
    def test_japan_live_clock(self) -> None:
        response = client.get("/time", params={"country": "Japan"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["country"], "Japan")
        self.assertEqual(body["country_code"], "JP")
        clock = body["timezones"][0]
        self.assertEqual(clock["timezone"], "Asia/Tokyo")
        self.assertEqual(clock["utc_offset"], "+09:00")
        local = datetime.fromisoformat(clock["local_time"])
        expected = datetime.now(ZoneInfo("Asia/Tokyo"))
        self.assertLess(abs((local - expected).total_seconds()), 5)

    def test_code_and_alias(self) -> None:
        response = client.get("/time", params={"country": "bd"})

        self.assertEqual(response.status_code, 200)
        clock = response.json()["timezones"][0]
        self.assertEqual(clock["timezone"], "Asia/Dhaka")
        self.assertEqual(clock["utc_offset"], "+06:00")

    def test_unknown_country(self) -> None:
        response = client.get("/time", params={"country": "Narnia"})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["error"],
            "Unknown country 'Narnia'. Use an English country name or an ISO code such as JP.",
        )

    def test_blank_country(self) -> None:
        response = client.get("/time", params={"country": "   "})

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "country must not be empty")

    def test_missing_country(self) -> None:
        response = client.get("/time")

        self.assertEqual(response.status_code, 422)

    def test_rejects_long_country(self) -> None:
        response = client.get("/time", params={"country": "A" * 101})

        self.assertEqual(response.status_code, 422)


class TestRootAndHealth(unittest.TestCase):
    def test_root(self) -> None:
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "description": "Current civil time for a country, in each of its time zones.",
                "sample_path": "/time?country=Japan",
            },
        )

    def test_health(self) -> None:
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ready(self) -> None:
        response = client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready"})


if __name__ == "__main__":
    unittest.main()
