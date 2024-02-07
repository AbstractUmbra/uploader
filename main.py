from __future__ import annotations

import pathlib
from random import choice
from secrets import token_urlsafe
from typing import NamedTuple

import aiohttp
import asyncpg
import toml
import uvicorn
from fastapi import FastAPI, File, Form, Header, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials  # noqa: TCH002

import api_token
from types_ import Config, ConfigFile, UploaderRequest, UploaderState  # noqa: TCH001


class UploaderApp(FastAPI):
    state: UploaderState  # type: ignore

    def __init__(self) -> None:
        super().__init__(
            title="CDN",
            debug=False,
            docs_url=None,
            redoc_url=None,
            on_startup=[self.app_startup],
        )
        self._config: Config = CONFIG

    async def app_startup(self) -> None:
        self.state.db = await asyncpg.create_pool(self._config["database"]["dsn"], max_inactive_connection_lifetime=0)  # type: ignore # override for protocol use
        assert self.state.db

        with pathlib.Path(self._config["database"]["schema_file"]).open() as schema:
            await self.state.db.execute(schema.read())

    async def send_to_webhook(self, data: bytes) -> bytes:
        form = aiohttp.FormData()
        form.add_field(
            name="file",
            value=data,
            filename="image.png",
            content_type="application/octet-stream",
        )
        async with aiohttp.ClientSession() as session, session.post(self._config["webhook"]["url"], data=form) as response:
            data = await response.json()

        return data

    def verify_auth(
        self,
        authentication: HTTPAuthorizationCredentials,
    ) -> tuple[bool, User] | None:
        user_id = api_token.get_user_id(authentication.credentials)
        for user, data in self._config["users"].items():
            if data["id"] == user_id:
                return data["token"] == authentication.credentials, User(user, data["id"], data["token"])
        return None


class User(NamedTuple):
    name: str
    id: int
    token: str


def gen_filename(length: int = 16, *, user: User) -> str:
    name = token_urlsafe(length).replace("-", "")

    path = ROOT_PATH / user.name / name
    while path.exists():
        return gen_filename(length, user=user)

    return name


FILETYPE_MAPPING: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "audio/mp4": ".m4a",
    "audio/mp3": ".mp3",
    "video/webm": ".webm",
}

INSERT_QUERY: str = "INSERT INTO images (author, filename, deletion_id) VALUES ($1, $2, $3);"
INSERT_AUDIO_QUERY: str = (
    "INSERT INTO audio (author, filename, title, soundgasm_author, deletion_id) VALUES ($1, $2, $3, $4, $5);"
)

DELETE_QUERY: str = "DELETE FROM images WHERE deletion_id = $1 AND author = $2 RETURNING filename;"
AUTH: HTTPBearer = HTTPBearer()
CONFIG: Config = toml.load(pathlib.Path("config.toml"))  # type: ignore # narrowing

ROOT_PATH: pathlib.Path = pathlib.Path("/etc/images/")
AUDIO_PATH: pathlib.Path = pathlib.Path("/etc/audio/")

CONFIG_FILE_JSON: ConfigFile = {
    "Version": "14.0.1",
    "Name": "Personal",
    "DestinationType": "ImageUploader, FileUploader",
    "RequestMethod": "POST",
    "RequestURL": "https://upload.umbra-is.gay/file",
    "Headers": {"Authorization": "Bearer {token}"},
    "Body": "MultipartFormData",
    "FileFormName": "image",
    "URL": "{json:image}",
    "DeletionURL": "{json:delete}",
}


app = UploaderApp()


@app.post("/config", status_code=202)
async def request_config(
    request: UploaderRequest,
    authorization: HTTPAuthorizationCredentials = Security(AUTH),
) -> JSONResponse:
    if not authorization or not authorization.credentials:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ret = request.app.verify_auth(authorization)
    if ret is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    authed, user = ret

    if not authed:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ret = CONFIG_FILE_JSON.copy()
    ret["Headers"]["Authorization"] = f"Bearer {user.token}"
    ret["Name"] = f"{user.name.title()}'s uploader config"
    return JSONResponse(ret)


@app.post("/file", status_code=201)
async def post_file(
    request: UploaderRequest,
    image: UploadFile,
    authorization: HTTPAuthorizationCredentials = Security(AUTH),
    preserve: bool | None = Header(False),
) -> JSONResponse:
    if not authorization or not authorization.credentials:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ret = request.app.verify_auth(authorization)
    if ret is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    authed, user = ret

    if not authed:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not image or len(data := await image.read()) == 0:
        return JSONResponse({"error": "Empty data"}, status_code=400)
    if not image.content_type:
        return JSONResponse({"error": "Unknown or missing content type"}, status_code=400)

    new_path_name = gen_filename(user=user)
    new_file_name = f"{new_path_name}{FILETYPE_MAPPING[image.content_type]}"
    new_path: pathlib.Path = ROOT_PATH / user.name / new_file_name

    with new_path.open("wb") as dump:
        await image.seek(0)
        dump.write(data)

    if preserve is True:
        new_path.symlink_to(ROOT_PATH / user.name / "preserve" / new_file_name, target_is_directory=False)
        await request.app.send_to_webhook(data)

    url = choice(request.app._config["web"][user.name])  # type: ignore
    delete = gen_filename(20, user=user)

    async with request.app.state.db.acquire() as conn, conn.transaction():
        await conn.fetchrow(INSERT_QUERY, user.id, new_file_name, delete)

    return JSONResponse(
        {
            "image": f"{url}/{new_file_name}",
            "delete": f"https://upload.umbra-is.gay/file/{delete}?user_id={user.id}",
            "type": image.content_type,
            "size": len(data),
        },
        status_code=201,
    )


@app.post("/audio", status_code=201)
async def post_audio(
    request: UploaderRequest,
    image: UploadFile = File(None),
    title: str | None = Form(None),
    soundgasm_author: str | None = Form(None),
    authorization: HTTPAuthorizationCredentials = Security(AUTH),
) -> JSONResponse:
    if not authorization or not authorization.credentials:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    ret = request.app.verify_auth(authorization)
    if ret is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    authed, user = ret

    if not authed:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not image or len(data := await image.read()) == 0:
        return JSONResponse({"error": "Empty data"}, status_code=400)
    if not image.content_type:
        return JSONResponse({"error": "Unknown or missing content type"}, status_code=400)

    new_path_name = gen_filename(user=user)
    new_file_name = f"{new_path_name}{FILETYPE_MAPPING[image.content_type]}"

    new_path: pathlib.Path = AUDIO_PATH / new_file_name
    with new_path.open("wb") as dump:
        await image.seek(0)
        dump.write(data)

    url = "https://audio.saikoro.moe"
    delete = gen_filename(20, user=user)

    async with request.app.state.db.acquire() as conn, conn.transaction():
        await conn.fetchrow(
            INSERT_AUDIO_QUERY,
            user.id,
            new_file_name,
            title,
            soundgasm_author,
            delete,
        )

    return JSONResponse(
        {
            "url": f"{url}/{new_file_name}",
            "title": title if title else "",
            "author": soundgasm_author if soundgasm_author else "",
            "delete": f"https://upload.umbra-is.gay/file/{delete}?user_id={user.id}",
            "type": image.content_type,
            "size": len(data),
        },
        status_code=201,
    )


@app.get("/file/{file_name}", status_code=200)
async def del_image(request: UploaderRequest, file_name: str, user_id: int) -> JSONResponse:
    user = None
    for user_, data in request.app._config["users"].items():  # type: ignore
        if data["id"] == user_id:
            user = user_
            break

    if user is None:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    record = await request.app.state.db.fetchrow(DELETE_QUERY, file_name, user_id)
    if not record:
        return JSONResponse({"error": "Unauthorized."}, status_code=401)

    existing_path: pathlib.Path = ROOT_PATH / user / record["filename"]
    if existing_path.exists():
        existing_path.unlink()
    return JSONResponse({"delete": "OK"}, status_code=200)


if __name__ == "__main__":
    uvicorn.run(app=app, host="0.0.0.0", port=9000, forwarded_allow_ips="*", proxy_headers=True)  # type: ignore
