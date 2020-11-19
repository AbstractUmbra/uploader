import pathlib
from random import choice
from secrets import token_urlsafe

import asyncpg
import toml
from fastapi import FastAPI, File, Security, UploadFile
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

import api_token

auth = HTTPBearer()
config = toml.load(pathlib.Path("config.toml"))

app = FastAPI(title="CDN")
root_path = pathlib.Path("/etc/images/")


def gen_filename(length: int = 10):
    return token_urlsafe(length).replace("-", "")


def verify_auth(authentication: Security(auth)):
    user_id = api_token.get_user_id(authentication.credentials)
    if user := config['users'].get(str(user_id), None):
        return user['token'] == authentication.credentials


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

    if not image or len((data := await image.read())) == 0:
        return JSONResponse({"error": "Empty data"}, status_code=400)

    user_id = api_token.get_user_id(authorization.credentials)
    user = config['users'].get(str(user_id))
    username = user['name']

    new_path_name = gen_filename()
    new_file_name = f"{new_path_name}{filetype_mapping[image.content_type]}"
    new_path = f"{root_path}/{username}/{new_file_name}"

    with open(f"{new_path}", "wb") as dump:
        await image.seek(0)
        dump.write(data)

    url = choice(config['web']['url'])

    return JSONResponse({"image": f"{url}/{username}/{new_file_name}", "type": image.content_type, "size": len(data)}, status_code=201)


@app.on_event("startup")
async def app_startup():
    app.state.db = await asyncpg.create_pool(config['database']['dsn'], max_inactive_connection_lifetime=0)
    with open(pathlib.Path(config['database']['schema'])) as schema:
        await app.state.db.execute(schema.read())
