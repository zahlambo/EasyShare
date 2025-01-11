from datetime import datetime
import os
import uuid
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse


load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR")

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

@router.post("/")
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

    file_link = f"/files/serve/{unique_id}"  # One unique link for all the files
    return {"message": "Files uploaded successfully", "file_link": file_link}


@router.get("/json/{unique_id}")
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
        download_link = f"/files/download/{unique_id}/{original_filename}"  # Create the proper download link
        files.append({
            "filename": original_filename,
            "download_link": download_link
        })

    # Return the JSON response with the list of files
    return {"files": files}


@router.get("/serve/{unique_id}", response_class=HTMLResponse)
async def serve_files_html(unique_id: str):
    # Serve the static HTML page for files
    with open("static/files.html", "r") as f:
        print(f)
        html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)


@router.get("/download/{unique_id}/{file_name}")
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