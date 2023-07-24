from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Literal, Protocol, Sequence, TypedDict

from fastapi import Request
from starlette.datastructures import State as _State

if TYPE_CHECKING:
    from types import TracebackType

    from asyncpg import Connection, Record

    from main import UploaderApp


class UploaderState(_State):
    db: DatabaseProtocol


class UploaderRequest(Request):
    @property
    def app(self) -> UploaderApp:
        ...


class ConnectionContextManager(Protocol):
    async def __aenter__(self) -> Connection[Record]:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...


class TransactionContextManager(Protocol):
    async def __aenter__(self) -> Connection[Record]:
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

    def release(self, connection: Connection[Record]) -> None:
        ...

    def transaction(self) -> TransactionContextManager:
        ...


class _ConfigHeaders(TypedDict):
    Authorization: str


class ConfigFile(TypedDict):
    Version: str
    Name: str
    DestinationType: Literal["ImageUploader, FileUploader"]
    RequestMethod: Literal["POST"]
    RequestURL: Literal["https://upload.umbra-is.gay/file"]
    Headers: _ConfigHeaders
    Body: Literal["MultipartFormData"]
    FileFormName: Literal["image"]
    URL: str
    DeletionURL: str
