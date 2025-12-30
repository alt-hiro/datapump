# datapump

`datapump` runs dbt-compiled SQL and exports the results to CSV. It can optionally upload CSVs to Amazon S3 or Azure Blob Storage.

## Requirements

- Python 3.9+
- dbt project with `dbt compile` executed
- Database drivers
  - Postgres: `psycopg2-binary`
  - SQL Server: an installed ODBC driver (default: `ODBC Driver 18 for SQL Server`)
  - MySQL: `PyMySQL`
  - Oracle: `oracledb` client libraries (Instant Client if needed)

## Installation

```bash
pip install -e .
```

## Quick start

From your dbt project directory:

```bash
dbt compile

datapump run \
  --select my_model,other_model \
  --output-dir target/datapump \
  --gzip \
  --s3-bucket my-bucket \
  --s3-prefix exports/
```

### Azure Blob upload

```bash
datapump run \
  --azure-container my-container \
  --azure-connection-string "DefaultEndpointsProtocol=..."
```

## How it works

1. `datapump run` reads `target/manifest.json` and collects compiled SQL for dbt models.
2. It connects to your warehouse based on `profiles.yml` (Postgres, SQL Server, MySQL, Oracle).
3. Query results stream to CSV using cursor fetches (`--fetch-size`, default 10,000).
4. Optional upload to S3 or Azure Blob.

## Options

- `--project-dir`: dbt project directory (default: `.`)
- `--profiles-dir`: dbt profiles directory (default: `~/.dbt`)
- `--profile`: dbt profile name (optional; inferred from `dbt_project.yml` when possible)
- `--target`: dbt target name (optional; defaults to profile target)
- `--select`: Comma-separated model names to export (default: all compiled models)
- `--output-dir`: Output directory for CSVs (default: `target/datapump`)
- `--local`: Skip object storage uploads (keeps files locally only)
- `--gzip`: Compress CSV outputs with gzip
- `--s3-bucket` / `--s3-prefix`: Upload to S3
- `--azure-container` / `--azure-connection-string`: Upload to Azure Blob
- `--fetch-size`: Rows per fetch (default: 10000)

## Notes

- Run `dbt compile` before `datapump run`; it relies on compiled SQL in `target/manifest.json`.
- For SQL Server, set `driver` in your profile if you use a different ODBC driver name.
