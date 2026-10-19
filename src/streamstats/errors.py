"""Ошибки, которые может вызвать программа."""


class StreamStatsError(Exception):
    """Общая ошибка анализатора."""


class UnsupportedFormatError(StreamStatsError):
    """Формат входного файла не поддерживается."""


class InvalidEventError(StreamStatsError):
    """В записи отсутствуют поля или неверные значения."""


class InvalidTimestampError(StreamStatsError):
    """Временная метка не соответствует ожидаемому формату."""


class CLIConfigError(StreamStatsError):
    """Некорректные пути или параметры запуска."""
