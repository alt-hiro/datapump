"""Run command for exporting models to CSV."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from datapump.db.executor import create_executor
from datapump.dbt.profiles import load_target_profile
from datapump.export.csv_writer import write_csv


@dataclass(frozen=True)
class ModelSpec:
    name: str
    sql: str


def run_models(
    models: Iterable[ModelSpec],
    *,
    profile_name: str | None = None,
    target_name: str | None = None,
    profiles_path: str | Path | None = None,
    output_dir: str | Path = "./exports",
) -> list[Path]:
    """Execute each model query and export the results to CSV."""

    profile = load_target_profile(
        profile_name=profile_name,
        target_name=target_name,
        profiles_path=profiles_path,
    )
    executor = create_executor(profile)
    output_paths: list[Path] = []
    try:
        for model in models:
            result = executor.execute(model.sql)
            output_path = Path(output_dir) / f"{model.name}.csv"
            output_paths.append(write_csv(result, output_path))
    finally:
        executor.close()
    return output_paths

  def run(_: argparse.Namespace) -> int:
    return 0
