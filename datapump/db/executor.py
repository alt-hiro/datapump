from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator

import psycopg2
import pyodbc


class DatabaseExecutor:
    def __init__(self, profile: Dict[str, Any], fetch_size: int = 10000) -> None:
        self.profile = profile
        self.fetch_size = fetch_size

    @contextmanager
    def execute(self, sql: str) -> Iterator[Any]:
        adapter = self.profile.get("type")
        if adapter == "postgres":
            with self._postgres_cursor() as cursor:
                cursor.execute(sql)
                yield cursor
            return
        if adapter in {"sqlserver", "mssql"}:
            with self._sqlserver_cursor() as cursor:
                cursor.execute(sql)
                yield cursor
            return

        raise ValueError(f"Unsupported adapter type: {adapter}")

    @contextmanager
    def _postgres_cursor(self) -> Iterator[Any]:
        conn = psycopg2.connect(
            host=self.profile.get("host"),
            user=self.profile.get("user"),
            password=self.profile.get("password"),
            dbname=self.profile.get("dbname"),
            port=self.profile.get("port", 5432),
        )
        try:
            cursor = conn.cursor()
            cursor.arraysize = self.fetch_size
            yield cursor
        finally:
            conn.close()

    @contextmanager
    def _sqlserver_cursor(self) -> Iterator[Any]:
        driver = self.profile.get("driver", "ODBC Driver 18 for SQL Server")
        server = self.profile.get("server")
        database = self.profile.get("database")
        user = self.profile.get("user")
        password = self.profile.get("password")
        port = self.profile.get("port")

        if port:
            server = f"{server},{port}"

        conn_str = (
            f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
            f"UID={user};PWD={password};TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        try:
            cursor = conn.cursor()
            cursor.arraysize = self.fetch_size
            yield cursor
        finally:
            conn.close()
