"""Проверка полей и представление одного события."""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidEventError, InvalidTimestampError


LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass
class Event:
    timestamp: datetime
    level: str
    source: str
    message: str


def validate_event(data):
    """Проверяет словарь и возвращает событие Event."""
    if not isinstance(data, dict):
        raise InvalidEventError("событие должно быть объектом")

    if None in data:
        raise InvalidEventError("лишние столбцы в CSV")

    for field in ("timestamp", "level", "source", "message"):
        if field not in data:
            raise InvalidEventError(f"отсутствует поле '{field}'")

    if not isinstance(data["timestamp"], str):
        raise InvalidTimestampError("timestamp должен быть строкой")

    text = data["timestamp"]
    if "T" not in text and " " not in text:
        raise InvalidTimestampError("timestamp должен включать время")

    # В Python 3.10 символ Z нужно заменить на смещение UTC.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError as error:
        raise InvalidTimestampError("неверный формат timestamp") from error

    # Даты без часового пояса считаем временем UTC.
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    timestamp = timestamp.astimezone(timezone.utc)

    level = data["level"]
    if not isinstance(level, str) or level not in LEVELS:
        raise InvalidEventError("неизвестный уровень события")

    source = data["source"]
    if not isinstance(source, str) or not source.strip():
        raise InvalidEventError("source должен быть непустой строкой")

    message = data["message"]
    if not isinstance(message, str):
        raise InvalidEventError("message должен быть строкой")

    return Event(timestamp, level, source.strip(), message)
