from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from neo import NeoCloud

import requests
from urllib3.util import parse_url

app = FastAPI()


@app.put("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    # Now you have the file contents, you can save it or process it as needed
    neo = NeoCloud()
    url = neo.get_presigned_url(file.filename)

    requests.put(url, data=contents)
    return JSONResponse(content={"direct": parse_url(url).url})
