"""Запуск программы через python -m streamstats."""

import argparse
import logging
import sys
from pathlib import Path

from .analysis import analyze_files
from .errors import CLIConfigError, StreamStatsError
from .report import build_report, report_to_json, save_report


def create_parser():
    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Анализ событий из CSV и JSONL",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    analyze = commands.add_parser("analyze", help="создать отчёт")
    analyze.add_argument("inputs", nargs="+", help="входные файлы")
    analyze.add_argument(
        "--format", required=True, choices=("csv", "jsonl"),
        help="формат входных данных",
    )
    analyze.add_argument("--output", help="путь для JSON-отчёта")
    analyze.add_argument(
        "--skip-invalid", action="store_true",
        help="пропускать некорректные записи",
    )
    return parser


def main(argv=None):
    arguments = create_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    try:
        if arguments.output:
            output_path = Path(arguments.output).resolve()
            for input_name in arguments.inputs:
                if output_path == Path(input_name).resolve():
                    raise CLIConfigError(
                        "выходной файл не должен совпадать с входным"
                    )

        stats = analyze_files(
            arguments.inputs,
            arguments.format,
            arguments.skip_invalid,
        )
        report = build_report(stats)

        if arguments.output:
            save_report(report, arguments.output)
        else:
            print(report_to_json(report))
    except (StreamStatsError, OSError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
