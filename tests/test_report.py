import json

from streamstats.analysis import Statistics
from streamstats.report import build_report, report_to_json, save_report


def test_report_with_cyrillic(tmp_path):
    stats = Statistics()
    stats.total_events = 1
    stats.source_counts["сервер"] = 1
    report = build_report(stats)

    text = report_to_json(report)
    assert "сервер" in text
    assert "\\u0441" not in text

    path = tmp_path / "report.json"
    save_report(report, path)
    assert json.loads(path.read_text(encoding="utf-8")) == report
