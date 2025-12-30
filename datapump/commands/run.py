import pathlib

from datapump.db.executor import DatabaseExecutor
from datapump.dbt.manifest import load_compiled_models
from datapump.dbt.profiles import load_profile
from datapump.export.csv_writer import write_csv
from datapump.storage.azure_blob import upload_to_azure_blob
from datapump.storage.s3 import upload_to_s3


def run(args) -> None:
    project_dir = pathlib.Path(args.project_dir).resolve()
    manifest_path = project_dir / "target" / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            "manifest.json not found. Run `dbt compile` before `datapump run`."
        )

    output_dir = pathlib.Path(args.output_dir or project_dir / "target" / "datapump")
    output_dir.mkdir(parents=True, exist_ok=True)

    models = load_compiled_models(manifest_path)
    selected = models
    if args.select:
        select_names = {name.strip() for name in args.select.split(",") if name.strip()}
        selected = {name: sql for name, sql in models.items() if name in select_names}

    profile = load_profile(project_dir, args.profiles_dir, args.profile, args.target)
    executor = DatabaseExecutor(profile, fetch_size=args.fetch_size)

    for model_name, sql in selected.items():
        csv_path = output_dir / f"{model_name}.csv"
        with executor.execute(sql) as cursor:
            write_csv(cursor, csv_path)

        if args.s3_bucket:
            key = f"{args.s3_prefix}{model_name}.csv"
            upload_to_s3(args.s3_bucket, key, csv_path)

        if args.azure_container and args.azure_connection_string:
            blob_name = f"{args.s3_prefix}{model_name}.csv"
            upload_to_azure_blob(
                args.azure_connection_string, args.azure_container, blob_name, csv_path
            )
