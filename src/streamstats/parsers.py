"""Чтение записей из CSV и JSONL."""

import csv
import json

from .errors import UnsupportedFormatError


def parse_csv(file):
    """Выдаёт номер строки, данные и сообщение об ошибке."""
    reader = csv.DictReader(file, strict=True)

    try:
        if reader.fieldnames is None:
            return
        required = ("timestamp", "level", "source", "message")

        if not all(field in reader.fieldnames for field in required):
            yield 1, None, "отсутствуют обязательные столбцы"
            return

        for row in reader:
            yield reader.line_num, row, None
    except csv.Error as error:
        # После ошибки кавычек CSV продолжение чтения ненадёжно.
        yield reader.line_num, None, f"неверная запись CSV: {error}"


def parse_jsonl(file):
    """Читает JSONL построчно, не прекращая работу на плохой строке."""
    for number, line in enumerate(file, start=1):
        try:
            data = json.loads(line)
        except json.JSONDecodeError as error:
            yield number, None, f"неверный JSON: {error.msg}"
        else:
            yield number, data, None


def get_parser(file_format):
    """Возвращает парсер по имени формата."""
    if file_format == "csv":
        return parse_csv
    if file_format == "jsonl":
        return parse_jsonl
    raise UnsupportedFormatError(
        f"формат '{file_format}' не поддерживается"
    )
