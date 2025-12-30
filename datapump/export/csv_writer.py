"""Streaming CSV writer for query results."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

from datapump.db.executor import QueryResult


def write_csv(
    result: QueryResult,
    output_path: str | Path,
    *,
    include_header: bool = True,
    encoding: str = "utf-8",
) -> Path:
    """Write a query result to CSV using streaming row iteration."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding=encoding) as handle:
        writer = csv.writer(handle)
        if include_header and result.columns:
            writer.writerow(result.columns)
        for row in _normalize_rows(result.rows):
            writer.writerow(row)
    return path


def _normalize_rows(rows: Iterable[Sequence]) -> Iterable[Sequence]:
    for row in rows:
        if isinstance(row, (list, tuple)):
            yield row
        else:
            yield tuple(row)
