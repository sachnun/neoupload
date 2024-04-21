from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from neo import NeoCloud

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
    filename: typing.Optional[str] = Form(None),
):
    responses = []
    for file in files:
        contents = await file.read()

        neo = NeoCloud()
        url = neo.get_presigned_url(filename or file.filename)
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
