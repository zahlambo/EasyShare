import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.utility.utils import decrypt_token

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR")

router = APIRouter(
    prefix="/files",
    tags=["Files"]
)

@router.post("/")
async def upload_files(request: Request, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    unique_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # For checking weather or not is the user logged in
    access_token = request.cookies.get("access_token")
    if access_token:
        user_id = decrypt_token(access_token).get("id")
    else:
        user_id = 0 # This is a default guest user inserted manually in database.
    
    for file in files:
        
        filesize = file.size

        # Insert the file details into the database
        # columns: id, file_id, filename, user_id, uploaded_at, is_public, size
        query = text(
            "INSERT INTO shared_files (file_id, filename, user_id, uploaded_at, is_public, size) "
            "VALUES (:file_id, :filename, :user_id, :uploaded_at, :is_public, :size)"
        )
        values = {
            "file_id": unique_id,
            "filename": file.filename,
            "user_id": user_id,
            "uploaded_at": timestamp,
            "is_public": True if user_id == 0 else False,
            "size": filesize
        }
        db.execute(query, values)
        db.commit()
        # Now retrieve the last inserted ID using LAST_INSERT_ID()
        last_inserted_id_query = text("SELECT LAST_INSERT_ID()")
        result = db.execute(last_inserted_id_query)
        inserted_id = result.scalar() 

        # Save each file with a unique composite filename but associate with the same tabe_id
        file_path = os.path.join(UPLOAD_DIR, inserted_id.__str__())
        with open(file_path, "wb") as f:
            f.write(await file.read())
    
    file_link = f"/files/serve/{unique_id}"  # One unique link for all the files
    return {"message": "Files uploaded successfully", "file_link": file_link}


@router.get("/list")
async def list_files(request: Request, db: Session = Depends(get_db)):
    # Try to get the user id
    user_id = decrypt_token(request.cookies.get("access_token")).get("id")

    # If the user is logged in, get the files uploaded by the user
    if user_id:
        query = text(
            "SELECT * FROM shared_files WHERE user_id = :user_id"
        )
        result = db.execute(query, {"user_id": user_id})

        # Get column names from the result
        columns = result.keys()
        
        files = result.fetchall()

        if not files:
            raise HTTPException(status_code=404, detail="No files found")

        # Convert each row to a dictionary using column names
        return [dict(zip(columns, file)) for file in files]
    else:
        raise HTTPException(status_code=401, detail="Unauthorized access")


@router.get("/json/{unique_id}")
async def get_files_json(request: Request,unique_id: str, db: Session = Depends(get_db)):
    # Find files matching the unique_id

     # For checking weather or not is the user logged in
    access_token = request.cookies.get("access_token")
    if access_token:
        user_id = decrypt_token(access_token).get("id")
        query = text("SELECT * FROM shared_files WHERE file_id = :file_id AND user_id = :user_id")
        values = {"file_id": unique_id, "user_id": user_id}
    else:
        user_id = 0 # This is a default guest user inserted manually in database.
        query = text("SELECT * FROM shared_files WHERE file_id = :file_id AND user_id = :user_id")
        values = {"file_id": unique_id, "user_id": user_id}

    # query = text("SELECT * FROM shared_files WHERE file_id = :file_id")
    # values = {"file_id": unique_id}
    
    # Execute the query
    result = db.execute(query, values)
    columns = result.keys()  
    files = result.fetchall()
    if not result:
        raise HTTPException(status_code=404, detail="No files found for this link")
    
    # Format results correctly as dictionaries
    search_results = [dict(zip(columns, file)) for file in files]  # Use .items() to get key-value pairs
    
    # Prepare the response
    files = []
    for file in search_results:
        original_filename = file["filename"]
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
    with open("src/templates/files.html", "r") as f:
        print(f)
        html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)


@router.get("/download/{unique_id}/{file_name}")
async def download_file(unique_id: str, file_name: str ,db: Session = Depends(get_db)):

    query = text("SELECT * FROM shared_files WHERE file_id = :file_id")
    values = {"file_id": unique_id}
    
    # Execute the query
    result = db.execute(query, values)
    columns = result.keys()  
    files = result.fetchall()    
    if not result:
        raise HTTPException(status_code=404, detail="No files found for this link")
    search_result = [
        [dict(zip(columns, file)) for file in files]
    ]
    if not search_result:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = os.path.join(UPLOAD_DIR, str(search_result[0][0]["id"]))
    original_filename = search_result[0][0]["filename"]
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=original_filename
    )