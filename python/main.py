import pathlib
from secrets import token_urlsafe

import asyncpg
import toml
from fastapi import FastAPI, File, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

auth = HTTPBearer()
config = toml.load(pathlib.Path("config.toml"))

app = FastAPI(title="CDN")
root_path = pathlib.Path("/etc/images/")


def gen_filename(length: int = 7):
    return token_urlsafe(length)


def verify_auth(authentication: Security(auth)):
    return authentication.credentials == config['users']['umbra']


filetype_mapping = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "video/mp4": ".mp4"
}


@app.post("/dickpic", status_code=201)
async def post_image(image: UploadFile = File(None), authorization: str = Security(auth)):
    if not authorization or not authorization.credentials:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not verify_auth(authorization):
        return JSONResponse({"error": "Unauthorized"}, status_code=403)

    if len(await image.read()) == 0:
        return JSONResponse({"error": "Empty data"}, status_code=400)

    new_path_name = gen_filename()
    new_file_name = f"{new_path_name}{filetype_mapping[image.content_type]}"
    new_path = f"{root_path}/{new_file_name}"

    with open(f"{new_path}", "wb") as dump:
        await image.seek(0)
        dump.write(await image.read())

    return JSONResponse({"image": f"{config['web']['url']}/{new_file_name}", "type": image.content_type}, status_code=201)


@app.on_event("startup")
async def app_startup():
    app.state.db = await asyncpg.create_pool(config['database']['dsn'], max_inactive_connection_lifetime=0)
    with open(pathlib.Path(config['database']['schema'])) as schema:
        await app.state.db.execute(schema.read())
