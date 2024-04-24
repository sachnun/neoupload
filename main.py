from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from neosign import get_presigned_url
from slugify import slugify

import aiohttp
import aiofiles
import gdown
import os
import typing
import shutil
import pyunpack
import uuid
import mimetypes
import logging
import asyncio

# import pyrfc6266

PWD = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(level=logging.DEBUG)

app = FastAPI(
    title="NeoUpload",
    description="An API to upload unlimited files with long-term storage.",
    version="0.1.1",
    docs_url="/",
)


def unpack_filename(filename: str) -> typing.Tuple[str, str]:
    try:
        f, e = filename.rsplit(".", 1)
    except ValueError:
        f, e = filename, ""

    return f, ("." + e if e else "")


@app.put("/upload")
async def upload_files(files: typing.List[UploadFile] = File(...)):
    async with aiohttp.ClientSession() as session:

        async def upload_file(file: UploadFile):
            logging.debug(f"Uploading {file.filename}...")
            contents = await file.read()
            filename, extention = unpack_filename(file.filename)

            url, direct = await get_presigned_url(slugify(filename) + extention)

            upload = await session.put(url, data=contents)
            return {
                "filename": filename + extention,
                "size": int(file.size),
                "mime": file.content_type,
                "upload": {
                    "status": True if upload.ok else False,
                    "url": direct,
                },
            }

        responses = await asyncio.gather(*(upload_file(file) for file in files))

    return JSONResponse(content=responses)


@app.put("/upload/remote")
async def gdrive_upload_files(
    url: str = Form(
        ..., description="The URL of the file to download (supports gdrive)."
    ),
    randomize: typing.Optional[bool] = Form(
        False, description="Randomize the filename."
    ),
):
    try:
        file = gdown.download(
            url=url, quiet=False, use_cookies=False, resume=True, fuzzy=True
        )
    except gdown.exceptions.FileURLRetrievalError as e:
        raise ValueError(str(e))

    files = []
    folder = os.path.join(PWD, str(uuid.uuid4()))

    try:
        pyunpack.Archive(file).extractall(folder, auto_create_dir=True)

        # check all subfolder, and move all file to folder_path
        for root, dirs, files in os.walk(folder):
            for f in files:
                shutil.move(os.path.join(root, f), folder)

        # delete all subfolder
        for root, dirs, files in os.walk(folder):
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

        # get all files path
        files = [os.path.join(folder, f) for f in os.listdir(folder)]
    except pyunpack.PatoolError:
        files = [file]  # if not archive, just use the file

    # upload async gather
    async with aiohttp.ClientSession() as session:

        async def upload_file(file: str):
            logging.debug(f"Uploading {file}...")
            async with aiofiles.open(file, mode="rb") as f:
                contents = await f.read()

            filename, extention = unpack_filename(os.path.basename(file))

            url, direct = await get_presigned_url(
                (str(uuid.uuid4()) if randomize else slugify(filename)) + extention
            )

            upload = await session.put(url, data=contents)
            return {
                "filename": filename + extention,
                "size": int(os.path.getsize(file)),
                "mime": mimetypes.guess_type(file)[0] or "application/octet-stream",
                "upload": {
                    "status": True if upload.ok else False,
                    "url": direct,
                },
            }

        responses = await asyncio.gather(*(upload_file(file) for file in files))

    # remove the folder after uploading if exists (with all files)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    # remove the file after uploading if exists
    if os.path.exists(file):
        os.remove(file)

    return JSONResponse(content=responses if len(responses) > 1 else responses[0])


# 500 internal server error
@app.exception_handler(Exception)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "reason": {
                "type": exc.__class__.__name__,
                "message": str(exc),
            },
        },
    )
