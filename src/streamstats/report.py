"""Подготовка и сохранение JSON-отчёта."""

import json
from pathlib import Path


def build_report(stats):
    """Создаёт словарь с итогами анализа."""
    ordered_errors = sorted(
        stats.error_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    top_sources = []
    for source, count in ordered_errors[:5]:
        top_sources.append({"source": source, "count": count})

    first = None
    last = None
    if stats.first_timestamp is not None:
        first = stats.first_timestamp.isoformat()
    if stats.last_timestamp is not None:
        last = stats.last_timestamp.isoformat()

    return {
        "total_events": stats.total_events,
        "by_level": stats.level_counts,
        "by_source": dict(sorted(stats.source_counts.items())),
        "top_error_sources": top_sources,
        "first_timestamp": first,
        "last_timestamp": last,
        "skipped_rows": stats.skipped_rows,
    }


def report_to_json(report):
    """Преобразует отчёт в читаемый JSON-текст."""
    return json.dumps(report, ensure_ascii=False, indent=2)


def save_report(report, path):
    """Записывает отчёт в файл с кодировкой UTF-8."""
    Path(path).write_text(report_to_json(report) + "\n", encoding="utf-8")
