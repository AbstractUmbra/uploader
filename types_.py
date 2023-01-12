from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Protocol, Sequence

from fastapi import Request
from starlette.datastructures import State as _State

if TYPE_CHECKING:
    from types import TracebackType

    from asyncpg import Connection

    from main import UploaderApp


class UploaderState(_State):
    db: DatabaseProtocol


class UploaderRequest(Request):
    app: UploaderApp


class ConnectionContextManager(Protocol):
    async def __aenter__(self) -> Connection:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...


class TransactionContextManager(Protocol):
    async def __aenter__(self) -> Connection:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...


class DatabaseProtocol(Protocol):
    async def execute(
        self, query: str, *args: Any, timeout: float | None = None
    ) -> str:
        ...

    async def fetch(
        self, query: str, *args: Any, timeout: float | None = None
    ) -> list[Any]:
        ...

    async def fetchrow(
        self, query: str, *args: Any, timeout: float | None = None
    ) -> Any | None:
        ...

    async def fetchval(
        self, query: str, *args: Any, timeout: float | None = None
    ) -> Any | None:
        ...

    async def executemany(
        self, query: str, args: Iterable[Sequence[Any]], *, timeout: float | None = None
    ) -> None:
        ...

    async def close(self) -> None:
        ...

    def acquire(self, *, timeout: float | None = None) -> ConnectionContextManager:
        ...

    def release(self, connection: Connection) -> None:
        ...

    def transaction(self) -> TransactionContextManager:
        ...
