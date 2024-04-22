from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from neo import NeoCloud
from slugify import slugify

import pyrfc6266
import requests
import gdown
import os
import typing
import shutil
import pyunpack
import random
import string

app = FastAPI(
    title="NeoUpload",
    description="An API to upload unlimited files with long-term storage.",
    version="0.1.0",
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
    neo = NeoCloud()
    responses = []
    for file in files:
        contents = await file.read()
        filename, extention = unpack_filename(file.filename)

        url, direct = neo.get_presigned_url(slugify(filename) + extention)

        upload = requests.put(url, data=contents)
        responses.append(
            {
                "filename": filename + extention,
                "size": file.size,
                "mime": file.content_type,
                "upload": {
                    "status": True if upload.ok else False,
                    "url": direct,
                },
            }
        )

    return JSONResponse(content=responses)


@app.put("/upload/remote")
async def remote_upload_files(
    url: str = Form(...),
):
    contents = requests.get(url)
    if not contents.ok:
        return JSONResponse(
            content={"error": "Failed to download the file from the given URL."},
            status_code=400,
        )

    filename, extention = unpack_filename(
        pyrfc6266.requests_response_to_filename(
            contents, enforce_content_disposition_type=True
        )
    )

    neo = NeoCloud()
    url, direct = neo.get_presigned_url(slugify(filename) + extention)

    upload = requests.put(url, data=contents.content)
    response = {
        "filename": filename + extention,
        "size": contents.headers.get("Content-Length") or len(contents.content),
        "mime": contents.headers.get("Content-Type").split(";")[0],  # remove charset
        "upload": {
            "status": True if upload.ok else False,
            "url": direct,
        },
    }

    return JSONResponse(content=response)


@app.put("/upload/remote/gdrive")
async def gdrive_upload_files(
    id: str = Form(...),
    extract: typing.Optional[bool] = Form(
        False, description="Extract all files before uploading."
    ),
):
    try:
        file = gdown.download(id=id, quiet=True, use_cookies=False)
    except gdown.exceptions.FileURLRetrievalError as e:
        return JSONResponse(
            content={
                "error": "Failed to download the file from the given Google Drive URL.",
                "reason": str(e),
            },
            status_code=400,
        )

    files = []

    if extract:
        folder = "/tmp/" + "".join(random.choices(string.ascii_lowercase, k=10))
        pyunpack.Archive(file).extractall(folder, auto_create_dir=True)

        # remove file after extracting
        os.remove(file)

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
    else:
        files.append(file)

    neo = NeoCloud()
    responses = []
    for file in files:
        with open(file, "rb") as f:
            contents = f.read()

        filename, extention = unpack_filename(os.path.basename(file))

        url, direct = neo.get_presigned_url(slugify(filename) + extention)

        upload = requests.put(url, data=contents)
        responses.append(
            {
                "filename": filename + extention,
                "size": os.path.getsize(file),
                "mime": "application/octet-stream",
                "upload": {
                    "status": True if upload.ok else False,
                    "url": direct,
                },
            }
        )

    # remove the folder after uploading if exists (with all files)
    if extract:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    return JSONResponse(content=responses)


# 500 internal server error
@app.exception_handler(Exception)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "reason": str(exc),
        },
    )
