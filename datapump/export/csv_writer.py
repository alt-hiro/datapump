import csv
from pathlib import Path
from typing import Any


def write_csv(cursor: Any, path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        columns = [desc[0] for desc in cursor.description]
        writer.writerow(columns)
        while True:
            rows = cursor.fetchmany(cursor.arraysize)
            if not rows:
                break
            writer.writerows(rows)
