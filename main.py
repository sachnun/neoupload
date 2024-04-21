from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from neo import NeoCloud
from slugify import slugify

import pyrfc6266
import requests
from urllib3.util import parse_url

import typing

app = FastAPI(
    title="NeoUpload",
    description="An API to upload unlimited files with long-term storage.",
    version="0.1.0",
    docs_url="/",
)


@app.put("/upload")
async def upload_files(
    files: typing.List[UploadFile] = File(...),
    filename: typing.Optional[str] = Form(None, description="Custom filename"),
):
    responses = []
    for file in files:
        contents = await file.read()
        filename, extention = (
            filename.rsplit(".", 1) if filename else file.filename.rsplit(".", 1)
        )

        neo = NeoCloud()
        url = neo.get_presigned_url(slugify(filename) + "." + extention)
        direct = (
            parse_url(url).scheme + "://" + parse_url(url).host + parse_url(url).path
        )

        requests.put(url, data=contents)
        responses.append(
            {
                "filename": file.filename,
                "size": file.size,
                "upload": {
                    "status": True,
                    "url": direct,
                },
            }
        )

    return JSONResponse(content=responses)


@app.put("/upload/remote")
async def remote_upload_files(
    url: str = Form(...),
    filename: typing.Optional[str] = Form(None, description="Custom filename"),
):
    contents = requests.get(url)
    raw_filename = pyrfc6266.requests_response_to_filename(
        contents, enforce_content_disposition_type=True
    )

    filename, extention = (
        filename.rsplit(".", 1) if filename else raw_filename.rsplit(".", 1)
    )

    neo = NeoCloud()
    url = neo.get_presigned_url(slugify(filename) + "." + extention)

    direct = parse_url(url).scheme + "://" + parse_url(url).host + parse_url(url).path

    requests.put(url, data=contents.content)
    response = {
        "filename": raw_filename,
        "size": len(contents.content),
        "upload": {
            "status": True,
            "url": direct,
        },
    }

    return JSONResponse(content=response)
