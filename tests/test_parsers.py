from io import StringIO

import pytest

from streamstats.errors import UnsupportedFormatError
from streamstats.parsers import get_parser, parse_csv, parse_jsonl


def test_parse_csv():
    source = StringIO(
        'timestamp,level,source,message\n'
        '2026-10-07T09:00:00Z,INFO,server,"Ошибка, повтор"\n'
    )
    items = list(parse_csv(source))
    assert len(items) == 1
    assert items[0][0] == 2
    assert items[0][1]["message"] == "Ошибка, повтор"
    assert items[0][2] is None


def test_csv_with_multiline_message():
    source = StringIO(
        'timestamp,level,source,message\n'
        '2026-10-07T09:00:00Z,INFO,server,"Первая\nВторая"\n',
        newline="",
    )
    number, event, error = next(parse_csv(source))
    assert number == 3
    assert event["message"] == "Первая\nВторая"
    assert error is None


def test_csv_missing_value():
    source = StringIO(
        "timestamp,level,source,message\n"
        "2026-10-07T09:00:00Z,INFO,server\n"
    )
    number, data, error = next(parse_csv(source))
    assert number == 2
    assert data["message"] is None
    assert error is None


def test_empty_csv():
    assert list(parse_csv(StringIO(""))) == []


def test_parse_jsonl():
    source = StringIO('{"source":"сервер","level":"INFO"}\n')
    number, data, error = next(parse_jsonl(source))
    assert number == 1
    assert data["source"] == "сервер"
    assert error is None


def test_jsonl_error_does_not_stop_generator():
    source = StringIO('не json\n{"source":"ok"}\n')
    rows = list(parse_jsonl(source))
    assert len(rows) == 2
    assert rows[0][0] == 1
    assert rows[0][2] is not None
    assert rows[1][1]["source"] == "ok"


def test_wrong_format():
    with pytest.raises(UnsupportedFormatError):
        get_parser("xml")
