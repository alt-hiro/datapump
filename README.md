# datapump

`datapump` runs dbt-compiled SQL and exports the results to CSV. It can optionally upload CSVs to Amazon S3 or Azure Blob Storage.

## Requirements

- Python 3.9+
- dbt project with `dbt compile` executed
- Database drivers for your adapter (Postgres or SQL Server)

## Installation

```bash
pip install -e .
```

## Usage

From your dbt project directory:

```bash
dbt compile

datapump run \
  --select my_model,other_model \
  --s3-bucket my-bucket \
  --s3-prefix exports/
```

### Azure Blob upload

```bash
datapump run \
  --azure-container my-container \
  --azure-connection-string "DefaultEndpointsProtocol=..."
```

## Options

- `--project-dir`: dbt project directory (default: `.`)
- `--profiles-dir`: dbt profiles directory (default: `~/.dbt`)
- `--profile`: dbt profile name (optional)
- `--target`: dbt target name (optional)
- `--select`: Comma-separated model names to export (default: all compiled models)
- `--output-dir`: Output directory for CSVs (default: `target/datapump`)
- `--s3-bucket` / `--s3-prefix`: Upload to S3
- `--azure-container` / `--azure-connection-string`: Upload to Azure Blob
- `--fetch-size`: Rows per fetch (default: 10000)
