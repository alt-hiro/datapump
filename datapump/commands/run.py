import logging
import pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed

from datapump.db.executor import DatabaseExecutor
from datapump.dbt.manifest import load_compiled_models
from datapump.dbt.profiles import load_profile
from datapump.export.csv_writer import write_csv
from datapump.storage.azure_blob import upload_to_azure_blob
from datapump.storage.s3 import upload_to_s3

logger = logging.getLogger(__name__)


def run(args) -> None:
    project_dir = pathlib.Path(args.project_dir).resolve()
    manifest_path = project_dir / "target" / "manifest.json"
    logger.debug("Resolved project directory to %s", project_dir)
    logger.debug("Looking for dbt manifest at %s", manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(
            "manifest.json not found. Run `dbt compile` before `datapump run`."
        )

    output_dir = pathlib.Path(args.output_dir or project_dir / "target" / "datapump")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Writing exports to %s", output_dir)

    models = load_compiled_models(manifest_path)
    selected = models
    if args.select:
        select_names = {name.strip() for name in args.select.split(",") if name.strip()}
        selected = {name: sql for name, sql in models.items() if name in select_names}
        logger.info("Selected %s models from --select", len(selected))
    else:
        logger.info("Selected all %s models", len(selected))

    profile = load_profile(project_dir, args.profiles_dir, args.profile, args.target)
    logger.info("Loaded dbt profile for adapter %s", profile.get("type"))
    executor = DatabaseExecutor(profile, fetch_size=args.fetch_size)
    logger.debug("Database fetch size set to %s", args.fetch_size)
    if args.parallelism < 1:
        raise ValueError("--parallelism must be at least 1")
    logger.info("Export parallelism set to %s", args.parallelism)

    extension = "csv.gz" if args.gzip else "csv"

    def export_model(model_name: str, sql: str) -> None:
        logger.info("Exporting model %s", model_name)
        logger.debug("SQL length for %s: %s characters", model_name, len(sql))
        csv_path = output_dir / f"{model_name}.{extension}"
        with executor.execute(sql) as cursor:
            write_csv(cursor, csv_path, gzip_enabled=args.gzip)
        logger.info("Wrote %s", csv_path)

        if args.local:
            logger.debug("Local-only mode enabled; skipping uploads for %s", model_name)
            continue

        if args.storage == "local":
            logger.debug("Storage set to local; skipping uploads for %s", model_name)
            continue

        if args.storage is None and args.s3_bucket:
            key = f"{args.s3_prefix}{model_name}.{extension}"
            upload_to_s3(args.s3_bucket, key, csv_path)
            logger.info("Uploaded %s to s3://%s/%s", model_name, args.s3_bucket, key)

        if args.storage is None and args.azure_container and args.azure_connection_string:
            blob_name = f"{args.s3_prefix}{model_name}.{extension}"
            upload_to_azure_blob(
                args.azure_connection_string, args.azure_container, blob_name, csv_path
            )
            logger.info(
                "Uploaded %s to Azure container %s as %s",
                model_name,
                args.azure_container,
                blob_name,
            )

        if args.storage == "aws_s3":
            if not args.s3_bucket:
                raise ValueError("--storage aws_s3 requires --s3-bucket")
            key = f"{args.s3_prefix}{model_name}.{extension}"
            upload_to_s3(args.s3_bucket, key, csv_path)
            logger.info("Uploaded %s to s3://%s/%s", model_name, args.s3_bucket, key)

        if args.storage == "azure_blob":
            if not args.azure_container or not args.azure_connection_string:
                raise ValueError(
                    "--storage azure_blob requires --azure-container and --azure-connection-string"
                )
            blob_name = f"{args.s3_prefix}{model_name}.{extension}"
            upload_to_azure_blob(
                args.azure_connection_string, args.azure_container, blob_name, csv_path
            )
            logger.info(
                "Uploaded %s to Azure container %s as %s",
                model_name,
                args.azure_container,
                blob_name,
            )

    items = list(selected.items())
    if args.parallelism == 1:
        for model_name, sql in items:
            export_model(model_name, sql)
        return

    with ThreadPoolExecutor(max_workers=args.parallelism) as pool:
        futures = [pool.submit(export_model, model_name, sql) for model_name, sql in items]
        for future in as_completed(futures):
            future.result()
