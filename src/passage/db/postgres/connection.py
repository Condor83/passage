from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from psycopg import Connection
from psycopg_pool import ConnectionPool


@dataclass(frozen=True, slots=True, repr=False)
class PostgresPoolConfig:
    request_dsn: str
    maintenance_dsn: str
    min_size: int = 1
    max_size: int = 4
    timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        if not self.request_dsn.strip() or not self.maintenance_dsn.strip():
            raise ValueError("request and maintenance DSNs are required")
        if self.request_dsn == self.maintenance_dsn:
            raise ValueError("request and maintenance DSNs must be distinct")
        if self.min_size < 0 or self.max_size < 1 or self.min_size > self.max_size:
            raise ValueError("invalid PostgreSQL pool size")
        if self.timeout_seconds <= 0:
            raise ValueError("PostgreSQL pool timeout must be positive")

    def __repr__(self) -> str:
        return (
            "PostgresPoolConfig(request_dsn=<redacted>, maintenance_dsn=<redacted>, "
            f"min_size={self.min_size}, max_size={self.max_size}, "
            f"timeout_seconds={self.timeout_seconds})"
        )


@dataclass(frozen=True, slots=True)
class RequestIdentity:
    issuer: str
    subject: str
    client: str

    def __post_init__(self) -> None:
        if not self.issuer.strip() or not self.subject.strip() or not self.client.strip():
            raise ValueError("issuer, subject, and client are required")


class PostgresPools:
    def __init__(self, config: PostgresPoolConfig) -> None:
        self.config = config
        self.request_pool = ConnectionPool(
            config.request_dsn,
            name="passage-request",
            min_size=config.min_size,
            max_size=config.max_size,
            timeout=config.timeout_seconds,
            open=False,
            kwargs={"autocommit": False},
        )
        self.maintenance_pool = ConnectionPool(
            config.maintenance_dsn,
            name="passage-maintenance",
            min_size=config.min_size,
            max_size=config.max_size,
            timeout=config.timeout_seconds,
            open=False,
            kwargs={"autocommit": False},
        )

    def open(self) -> None:
        try:
            self.request_pool.open(wait=True, timeout=self.config.timeout_seconds)
            self.maintenance_pool.open(wait=True, timeout=self.config.timeout_seconds)
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        self.request_pool.close()
        self.maintenance_pool.close()

    def __enter__(self) -> PostgresPools:
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def request(self, identity: RequestIdentity) -> Iterator[Connection[tuple[object, ...]]]:
        with (
            self.request_pool.connection() as connection,
            connection.transaction(),
        ):
            connection.execute(
                "select set_config('passage.issuer', %s, true)",
                (identity.issuer,),
            )
            connection.execute(
                "select set_config('passage.subject', %s, true)",
                (identity.subject,),
            )
            connection.execute(
                "select set_config('passage.client', %s, true)",
                (identity.client,),
            )
            yield connection

    @contextmanager
    def maintenance(self) -> Iterator[Connection[tuple[object, ...]]]:
        with (
            self.maintenance_pool.connection() as connection,
            connection.transaction(),
        ):
            yield connection
