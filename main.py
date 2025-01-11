import asyncio
import contextlib
import os
from contextlib import asynccontextmanager

from sqlalchemy import text

from src.database.database import get_db

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from src.routes.auth import router as auth_router
from src.routes.files import router as files_router
from src.routes.html import router as html_router

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Cleanup task for deleting old files
async def cleanup_old_files():
    db = next(get_db())

    # Function to clean up old files based on the timestamp condition
    async def delete_old_files():
        query = text("SELECT id FROM shared_files WHERE TIMESTAMPDIFF(HOUR, uploaded_at, NOW()) > 4;")
        result = db.execute(query).fetchall()

        file_ids_to_delete = {str(item[0]) for item in result}  # Set of file IDs to be deleted
        for file_id in file_ids_to_delete:
            file_path = os.path.join(UPLOAD_DIR, file_id)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted old file: {file_id}")
                except Exception as e:
                    print(f"Error deleting file {file_id}: {e}")
        
        # Remove corresponding entries from the database
        try:
            db.execute("DELETE FROM shared_files WHERE TIMESTAMPDIFF(HOUR, uploaded_at, NOW()) > 4;")
            db.commit()
        except Exception as e:
            print(f"Error cleaning up database: {e}")

    # Function to delete files not in the database
    async def delete_invalid_files():
        query = text("SELECT id FROM shared_files;")
        result = db.execute(query).fetchall()
        valid_file_ids = {str(item[0]) for item in result}  # Set of valid file IDs

        # Loop through all the files in the upload directory
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            file_id = os.path.splitext(filename)[0]  # Assuming file name is the file ID
            
            if file_id not in valid_file_ids:
                try:
                    os.remove(file_path)
                    print(f"Deleted orphan file: {file_id}")
                except Exception as e:
                    print(f"Error deleting orphan file {file_id}: {e}")

    # Run cleanup every hour
    while True:
        # Delete files older than 4 hours and clean up database
        await delete_old_files()

        # Delete orphaned files not found in the database
        await delete_invalid_files()

        # Wait for 1 hour before the next cleanup
        await asyncio.sleep(3600)  # Sleep for 1 hour


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


app.include_router(auth_router)
app.include_router(files_router)

# This should always be at the bottom.
app.include_router(html_router)

# Mount static files directory
app.mount("/static", StaticFiles(directory="src/static"), name="static")
