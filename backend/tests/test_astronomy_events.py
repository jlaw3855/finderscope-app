"""Tests for astronomy event search."""

from datetime import datetime, timedelta

from astronomy import Time

from app.services.astronomy_events import EVENT_WINDOW_DAYS, search_astronomy_events
from app.services.astronomy_time import time_to_utc_datetime


class TestAstronomyEvents:
    def test_events_sorted_by_start_at(self) -> None:
        events = search_astronomy_events(39.7392, -104.9903)
        starts = [event.start_at for event in events]
        assert starts == sorted(starts)

    def test_events_within_ninety_day_window(self) -> None:
        start = Time.Now()
        end_dt = time_to_utc_datetime(Time.AddDays(start, EVENT_WINDOW_DAYS))
        events = search_astronomy_events(39.7392, -104.9903, start_time=start)
        for event in events:
            assert event.start_at <= end_dt + timedelta(hours=1)

    def test_event_schema_fields(self) -> None:
        events = search_astronomy_events(37.13, -121.65)
        if not events:
            return
        event = events[0]
        assert event.id
        assert event.category in {
            "lunar_eclipse",
            "solar_eclipse",
            "transit",
            "conjunction",
            "opposition",
            "meteor_shower",
        }
        assert event.title
        assert isinstance(event.start_at, datetime)
        assert event.description

    def test_mercury_inferior_conjunction_in_window(self) -> None:
        start = Time.Make(2026, 6, 15, 0, 0, 0)
        events = search_astronomy_events(37.13, -121.65, start_time=start, window_days=30)
        titles = [event.title for event in events]
        assert any("Mercury inferior conjunction" in title for title in titles)

    def test_meteor_showers_in_ninety_day_window(self) -> None:
        start = Time.Make(2026, 7, 1, 0, 0, 0)
        events = search_astronomy_events(39.7392, -104.9903, start_time=start, window_days=90)
        meteor_events = [event for event in events if event.category == "meteor_shower"]
        assert any("Perseids" in event.title for event in meteor_events)
