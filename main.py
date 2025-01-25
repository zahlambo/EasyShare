import contextlib
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import os
from fastapi.responses import FileResponse
from fastapi import File, UploadFile
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uuid
import asyncio
from contextlib import asynccontextmanager

from starlette.responses import HTMLResponse

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Cleanup task for deleting old files
async def cleanup_old_files():
    while True:
        now = datetime.now()
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)

            # Ensure we only handle files
            if os.path.isfile(file_path):
                try:
                    # Extract timestamp from the filename
                    timestamp_str = filename.split("'___'")[-1]
                    file_time = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")

                    # Check if the file is older than 8 hours
                    if now - file_time > timedelta(hours=32) and os.path.exists(
                            file_path
                    ):
                        os.remove(file_path)
                        print(f"Deleted old file: {filename}")
                except Exception as e:
                    print(f"Error processing file {filename}: {e}")

        await asyncio.sleep(3600)  # Wait for 1 hour before running again


@asynccontextmanager
async def lifespan(app: FastAPI):
    cleanup_task = asyncio.create_task(cleanup_old_files())
    try:
        yield
    finally:
        # Shutdown logic: Cancel the cleanup task
        cleanup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload/")
async def upload_files(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    unique_id = str(uuid.uuid4())  # Generate a single unique ID for the set of files
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    for file in files:
        # Save each file with a unique composite filename but associate with the same unique_id
        filename = f"{file.filename}'@@@'{unique_id}'___'{timestamp}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

    file_link = f"/files/{unique_id}"  # One unique link for all the files
    return {"message": "Files uploaded successfully", "file_link": file_link}


@app.get("/files-json/{unique_id}")
async def get_files_json(unique_id: str):
    # Find files matching the unique_id
    search_results = [
        f for f in os.listdir(UPLOAD_DIR) if f"'@@@'{unique_id}" in f
    ]
    if not search_results:
        raise HTTPException(status_code=404, detail="No files found for this link")

    files = []
    for file in search_results:
        original_filename = file.split("'@@@'")[0]  # Clean up the filename
        download_link = f"/download/{unique_id}/{original_filename}"  # Create the proper download link
        files.append({
            "filename": original_filename,
            "download_link": download_link
        })

    # Return the JSON response with the list of files
    return {"files": files}


@app.get("/files/{unique_id}", response_class=HTMLResponse)
async def serve_files_html(unique_id: str):
    # Serve the static HTML page for files
    with open("static/files.html", "r") as f:
        print(f)
        html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)


@app.get("/download/{unique_id}/{file_name}")
async def download_file(unique_id: str, file_name: str):
    search_result = [
        f for f in os.listdir(UPLOAD_DIR)
        if f"'@@@'{unique_id}" in f and file_name in f
    ]
    if not search_result:
        raise HTTPException(status_code=404, detail="File not found")

    file_name = search_result[0]
    file_path = os.path.join(UPLOAD_DIR, file_name)
    original_filename = file_name.split("'@@@'")[0]
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=original_filename
    )

app.mount("/", StaticFiles(directory="static", html=True), name="static")
