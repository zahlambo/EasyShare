from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import TemplateNotFound

templates = Jinja2Templates(directory="src/templates")


router = APIRouter(
    prefix="",
    tags=["Frontend"]
)

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/{file_name}", response_class=HTMLResponse)
async def html_file(request: Request, file_name: str):
    try:
        return templates.TemplateResponse(f"{file_name}.html", {"request": request})
    except TemplateNotFound:
        raise HTTPException(status_code=404, detail="Page not found")