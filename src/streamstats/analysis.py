"""Подсчёт статистики по событиям из файлов."""

import logging
from pathlib import Path

from .errors import CLIConfigError, InvalidEventError, InvalidTimestampError
from .models import LEVELS, validate_event
from .parsers import get_parser


logger = logging.getLogger("streamstats")


class Statistics:
    """Хранит итоги обработки всех файлов."""

    def __init__(self):
        self.total_events = 0
        self.skipped_rows = 0
        self.level_counts = {level: 0 for level in LEVELS}
        self.source_counts = {}
        self.error_counts = {}
        self.first_timestamp = None
        self.last_timestamp = None

    def add_event(self, event):
        self.total_events += 1
        self.level_counts[event.level] += 1

        source = event.source
        self.source_counts[source] = self.source_counts.get(source, 0) + 1

        if event.level in ("ERROR", "CRITICAL"):
            self.error_counts[source] = self.error_counts.get(source, 0) + 1

        if self.first_timestamp is None:
            self.first_timestamp = event.timestamp
        elif event.timestamp < self.first_timestamp:
            self.first_timestamp = event.timestamp

        if self.last_timestamp is None:
            self.last_timestamp = event.timestamp
        elif event.timestamp > self.last_timestamp:
            self.last_timestamp = event.timestamp


def analyze_files(paths, file_format, skip_invalid=False):
    """Читает файлы по очереди и накапливает общую статистику."""
    parser = get_parser(file_format)
    stats = Statistics()

    for file_number, path in enumerate(paths, start=1):
        try:
            with Path(path).open(encoding="utf-8-sig", newline="") as file:
                for number, data, parse_error in parser(file):
                    try:
                        if parse_error is not None:
                            raise InvalidEventError(parse_error)
                        event = validate_event(data)
                    except (InvalidEventError, InvalidTimestampError) as error:
                        location = (
                            f"файл №{file_number}: {path}, строка {number}"
                        )
                        if not skip_invalid:
                            raise InvalidEventError(
                                f"{location}: {error}"
                            ) from error
                        logger.warning("%s: %s", location, error)
                        stats.skipped_rows += 1
                        continue

                    stats.add_event(event)
        except (OSError, UnicodeError) as error:
            raise CLIConfigError(
                f"не удалось прочитать файл '{path}': {error}"
            ) from error

    return stats
