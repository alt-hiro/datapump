"""Database execution interfaces for different adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from datapump.dbt.profiles import TargetProfile


class ExecutorError(Exception):
    """Raised when query execution fails."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: Iterable[Sequence]


class DbExecutor:
    """Base class for database executors."""

    def execute(self, sql: str) -> QueryResult:  # pragma: no cover - interface
        raise NotImplementedError

    def close(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class DbApiExecutor(DbExecutor):
    """Executor that uses a DB-API compatible connection."""

    def __init__(self, connection, fetch_size: int = 1000):
        self._connection = connection
        self._fetch_size = fetch_size

    def execute(self, sql: str) -> QueryResult:
        cursor = self._connection.cursor()
        cursor.execute(sql)
        columns = [description[0] for description in cursor.description or []]

        def row_stream() -> Iterator[Sequence]:
            while True:
                batch = cursor.fetchmany(self._fetch_size)
                if not batch:
                    break
                for row in batch:
                    yield row
            cursor.close()

        return QueryResult(columns=columns, rows=row_stream())

    def close(self) -> None:
        self._connection.close()


class PostgresExecutor(DbApiExecutor):
    """Postgres executor backed by psycopg2."""

    def __init__(self, config: dict):
        try:
            import psycopg2
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise ExecutorError("psycopg2 is required for Postgres execution") from exc
        connection = psycopg2.connect(
            host=config.get("host"),
            port=config.get("port"),
            user=config.get("user"),
            password=config.get("password"),
            dbname=config.get("dbname")
            or config.get("database")
            or config.get("db"),
        )
        super().__init__(connection)


class BigQueryExecutor(DbExecutor):
    """BigQuery executor backed by google-cloud-bigquery."""

    def __init__(self, config: dict):
        try:
            from google.cloud import bigquery
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise ExecutorError(
                "google-cloud-bigquery is required for BigQuery execution"
            ) from exc
        project = config.get("project") or config.get("project_id")
        self._client = bigquery.Client(project=project)
        self._job_config = bigquery.QueryJobConfig()

    def execute(self, sql: str) -> QueryResult:
        job = self._client.query(sql, job_config=self._job_config)
        result = job.result(page_size=1000)
        columns = [field.name for field in result.schema]
        return QueryResult(columns=columns, rows=(tuple(row) for row in result))

    def close(self) -> None:
        self._client.close()


class SnowflakeExecutor(DbApiExecutor):
    """Snowflake executor backed by snowflake-connector-python."""

    def __init__(self, config: dict):
        try:
            import snowflake.connector
        except ImportError as exc:  # pragma: no cover - depends on optional package
            raise ExecutorError(
                "snowflake-connector-python is required for Snowflake execution"
            ) from exc
        connection = snowflake.connector.connect(
            user=config.get("user"),
            password=config.get("password"),
            account=config.get("account"),
            warehouse=config.get("warehouse"),
            database=config.get("database"),
            schema=config.get("schema"),
            role=config.get("role"),
        )
        super().__init__(connection)


def create_executor(profile: TargetProfile) -> DbExecutor:
    adapter = profile.adapter_type.lower()
    if adapter in {"postgres", "postgresql"}:
        return PostgresExecutor(profile.config)
    if adapter in {"bigquery", "bq"}:
        return BigQueryExecutor(profile.config)
    if adapter in {"snowflake"}:
        return SnowflakeExecutor(profile.config)
    raise ExecutorError(f"unsupported adapter type: {profile.adapter_type}")
