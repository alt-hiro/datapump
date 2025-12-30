import argparse
import logging

from datapump.commands.run import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="datapump")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run dbt compiled SQL and export data")
    run_parser.add_argument("--project-dir", default=".", help="Path to dbt project directory")
    run_parser.add_argument("--profiles-dir", default=None, help="Path to dbt profiles directory")
    run_parser.add_argument("--profile", default=None, help="dbt profile name")
    run_parser.add_argument("--target", default=None, help="dbt target name")
    run_parser.add_argument("--select", default=None, help="Comma-separated model names to export")
    run_parser.add_argument("--output-dir", default=None, help="Directory to write CSVs")
    run_parser.add_argument(
        "--local",
        action="store_true",
        help="Skip object storage uploads and keep files locally only",
    )
    run_parser.add_argument(
        "--gzip",
        action="store_true",
        help="Compress CSV outputs with gzip",
    )
    run_parser.add_argument("--s3-bucket", default=None, help="S3 bucket for upload")
    run_parser.add_argument("--s3-prefix", default="", help="S3 key prefix")
    run_parser.add_argument("--azure-container", default=None, help="Azure Blob container name")
    run_parser.add_argument(
        "--azure-connection-string",
        default=None,
        help="Azure Blob connection string",
    )
    run_parser.add_argument(
        "--storage",
        choices=["aws_s3", "azure_blob", "local"],
        default=None,
        help="Explicit storage backend to use (aws_s3, azure_blob, local)",
    )
    run_parser.add_argument(
        "--parallelism",
        type=int,
        default=1,
        help="Number of models to export in parallel",
    )
    run_parser.add_argument("--fetch-size", type=int, default=10000, help="Rows per fetch")
    run_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.WARNING,
            format="%(levelname)s:%(name)s:%(message)s",
        )
        run(args)


if __name__ == "__main__":
    main()
