from fastapi import FastAPI, UploadFile, File
from neo import NeoCloud

import requests

app = FastAPI()

@app.put("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    # Now you have the file contents, you can save it or process it as needed
    neo = NeoCloud()
    url = neo.get_presigned_url(file.filename)

    requests.put(url, data=contents)
    return url

