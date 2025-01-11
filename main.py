import asyncio
import contextlib
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from src.routes.auth import router as auth_router
from src.routes.files import router as files_router

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR")
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


app.include_router(auth_router)
app.include_router(files_router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
