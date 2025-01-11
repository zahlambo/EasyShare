import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from src.database.database import get_db

from dotenv import load_dotenv
from fastapi import FastAPI,Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
    while True:
        now = datetime.now()
        query = text("SELECT id FROM shared_files WHERE TIMESTAMPDIFF(HOUR, uploaded_at, NOW()) > 4;")
        result = db.execute(query).fetchall()
        result[:] = [str(item[0]) for item in result]

        for file_id in result:
            file_path = os.path.join(UPLOAD_DIR, file_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted old file: {file_id}")
        db.execute("DELETE FROM shared_files WHERE TIMESTAMPDIFF(HOUR, uploaded_at, NOW()) > 4;")
        db.commit()
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

# This should always be at the bottom.
app.include_router(html_router)

# Mount static files directory
app.mount("/static", StaticFiles(directory="src/static"), name="static")
