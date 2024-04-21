from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.put("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    # Now you have the file contents, you can save it or process it as needed
    return {"filename": file.filename}