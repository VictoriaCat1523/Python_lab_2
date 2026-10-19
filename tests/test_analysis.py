import logging

import pytest

from streamstats.analysis import analyze_files
from streamstats.errors import InvalidEventError
from streamstats.report import build_report


HEADER = "timestamp,level,source,message\n"


def create_csv(path, rows):
    path.write_text(HEADER + rows, encoding="utf-8")
    return path


def test_statistics_from_multiple_files(tmp_path):
    first = create_csv(
        tmp_path / "first.csv",
        "2026-10-07T12:00:00+03:00,ERROR,db,Сбой\n"
        "2026-10-07T12:01:00+03:00,INFO,api,Готово\n",
    )
    second = create_csv(
        tmp_path / "second.csv",
        "2026-10-07T08:00:00+00:00,CRITICAL,db,Сбой\n"
        "2026-10-07T15:00:00+03:00,ERROR,api,Сбой\n",
    )
    stats = analyze_files([first, second], "csv")
    report = build_report(stats)
    assert report["total_events"] == 4
    assert report["by_level"]["ERROR"] == 2
    assert report["by_source"] == {"api": 2, "db": 2}
    assert report["top_error_sources"][0] == {"source": "db", "count": 2}
    assert report["first_timestamp"] == "2026-10-07T08:00:00+00:00"
    assert report["last_timestamp"] == "2026-10-07T12:00:00+00:00"


def test_empty_file(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    report = build_report(analyze_files([path], "jsonl"))
    assert report["total_events"] == 0
    assert report["first_timestamp"] is None
    assert report["top_error_sources"] == []
    assert report["skipped_rows"] == 0


def test_broken_csv_without_skip(tmp_path):
    path = create_csv(
        tmp_path / "events.csv",
        "2026-10-07T12:00:00Z,INFO,server\n",
    )
    with pytest.raises(InvalidEventError, match=r"events.csv, строка 2"):
        analyze_files([path], "csv")


def test_skip_broken_csv_and_continue(tmp_path, caplog):
    path = create_csv(
        tmp_path / "events.csv",
        "2026-10-07T12:00:00Z,INFO,server\n"
        "2026-10-07T12:01:00Z,ERROR,db,Сбой\n",
    )
    with caplog.at_level(logging.WARNING, logger="streamstats"):
        stats = analyze_files([path], "csv", skip_invalid=True)
    assert stats.skipped_rows == 1
    assert stats.total_events == 1
    assert "строка 2" in caplog.text


def test_skip_broken_jsonl_and_continue(tmp_path, caplog):
    path = tmp_path / "events.jsonl"
    path.write_text(
        "{ошибка}\n"
        '{"timestamp":"2026-10-07T09:00:00Z",'
        '"level":"INFO","source":"сервис","message":"Готово"}\n',
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING, logger="streamstats"):
        stats = analyze_files([path], "jsonl", skip_invalid=True)
    assert stats.skipped_rows == 1
    assert stats.total_events == 1
    assert stats.source_counts == {"сервис": 1}
    assert "строка 1" in caplog.text


def test_top_errors_use_source_name_on_equal_counts(tmp_path):
    path = create_csv(
        tmp_path / "events.csv",
        "2026-10-07T09:00:00Z,ERROR,zeta,Сбой\n"
        "2026-10-07T09:01:00Z,CRITICAL,alpha,Сбой\n",
    )
    report = build_report(analyze_files([path], "csv"))
    assert report["top_error_sources"] == [
        {"source": "alpha", "count": 1},
        {"source": "zeta", "count": 1},
    ]


def test_header_only(tmp_path):
    path = create_csv(tmp_path / "only_header.csv", "")
    assert analyze_files([path], "csv").total_events == 0


def test_error_contains_input_file_number(tmp_path):
    first = create_csv(
        tmp_path / "first.csv",
        "2026-10-07T09:00:00Z,INFO,server,ok\n",
    )
    second = create_csv(
        tmp_path / "second.csv",
        "2026-10-07T10:00:00Z,UNKNOWN,server,bad\n",
    )
    with pytest.raises(InvalidEventError, match="файл №2"):
        analyze_files([first, second], "csv")
