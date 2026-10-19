import json
import subprocess
import sys


def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, "-m", "streamstats", *map(str, arguments)],
        text=True,
        capture_output=True,
        check=False,
    )


def test_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "analyze" in result.stdout


def test_cli_saves_file(tmp_path):
    source = tmp_path / "events.jsonl"
    output = tmp_path / "report.json"
    source.write_text(
        '{"timestamp":"2026-10-07T09:00:00Z",'
        '"level":"ERROR","source":"server","message":"ошибка"}\n',
        encoding="utf-8",
    )
    result = run_cli(
        "analyze", source, "--format", "jsonl", "--output", output,
    )
    assert result.returncode == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["total_events"] == 1
    assert report["by_level"]["ERROR"] == 1


def test_cli_invalid_row_returns_code_2(tmp_path):
    source = tmp_path / "bad.jsonl"
    source.write_text("bad json\n", encoding="utf-8")
    result = run_cli("analyze", source, "--format", "jsonl")
    assert result.returncode == 2
    assert "строка 1" in result.stderr


def test_cli_skip_invalid_prints_json(tmp_path):
    source = tmp_path / "events.jsonl"
    source.write_text(
        'wrong\n'
        '{"timestamp":"2026-10-07T09:00:00Z",'
        '"level":"INFO","source":"api","message":"ok"}\n',
        encoding="utf-8",
    )
    result = run_cli(
        "analyze", source, "--format", "jsonl", "--skip-invalid",
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["skipped_rows"] == 1
    assert "WARNING" in result.stderr


def test_cli_does_not_overwrite_input(tmp_path):
    source = tmp_path / "events.jsonl"
    content = '{"source":"server"}\n'
    source.write_text(content, encoding="utf-8")
    result = run_cli(
        "analyze", source, "--format", "jsonl", "--output", source,
    )
    assert result.returncode == 2
    assert source.read_text(encoding="utf-8") == content


def test_cli_missing_file(tmp_path):
    source = tmp_path / "not_found.csv"
    result = run_cli("analyze", source, "--format", "csv")
    assert result.returncode == 2
    assert "not_found.csv" in result.stderr
