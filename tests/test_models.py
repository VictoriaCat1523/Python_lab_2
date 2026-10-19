from datetime import datetime, timezone

import pytest

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import Event, validate_event


@pytest.fixture
def valid_data():
    return {
        "timestamp": "2026-10-07T12:00:00+03:00",
        "level": "INFO",
        "source": " server ",
        "message": "Запуск",
    }


def test_valid_event(valid_data):
    event = validate_event(valid_data)
    assert isinstance(event, Event)
    assert event.timestamp == datetime(2026, 10, 7, 9, tzinfo=timezone.utc)
    assert event.source == "server"
    assert event.message == "Запуск"


def test_timestamp_without_timezone_is_utc(valid_data):
    valid_data["timestamp"] = "2026-10-07T09:00:00"
    event = validate_event(valid_data)
    assert event.timestamp.utcoffset().total_seconds() == 0


@pytest.mark.parametrize("missing", [
    "timestamp", "level", "source", "message",
])
def test_missing_field(valid_data, missing):
    del valid_data[missing]
    with pytest.raises(InvalidEventError, match=missing):
        validate_event(valid_data)


@pytest.mark.parametrize("value", ["", "   ", None, 4])
def test_invalid_source(valid_data, value):
    valid_data["source"] = value
    with pytest.raises(InvalidEventError):
        validate_event(valid_data)


@pytest.mark.parametrize("value", ["warn", "FATAL", 5, None])
def test_invalid_level(valid_data, value):
    valid_data["level"] = value
    with pytest.raises(InvalidEventError):
        validate_event(valid_data)


def test_empty_message_is_valid(valid_data):
    valid_data["message"] = ""
    assert validate_event(valid_data).message == ""


def test_wrong_message_type(valid_data):
    valid_data["message"] = 12
    with pytest.raises(InvalidEventError):
        validate_event(valid_data)


@pytest.mark.parametrize(
    "value", ["вчера", "2026-14-07T10:00:00", "2026-10-07", 6],
)
def test_invalid_timestamp(valid_data, value):
    valid_data["timestamp"] = value
    with pytest.raises(InvalidTimestampError):
        validate_event(valid_data)


def test_event_must_be_dict():
    with pytest.raises(InvalidEventError):
        validate_event(["INFO", "server"])


def test_extra_csv_columns(valid_data):
    valid_data[None] = ["лишнее"]
    with pytest.raises(InvalidEventError):
        validate_event(valid_data)


def test_z_suffix(valid_data):
    valid_data["timestamp"] = "2026-10-07T09:00:00Z"
    event = validate_event(valid_data)
    assert event.timestamp.hour == 9
