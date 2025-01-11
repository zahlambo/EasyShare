from fastapi import APIRouter, HTTPException, Depends, status, Response, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.database.database import get_db
from src.database.models import User
from src.schemas.schemas import UserLogin, UserRegister, Token
from src.utility.utils import create_access_token, get_current_timestamp, hash_password, verify_password

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# Constants for Cookie Settings
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE = 60 * 30  # 30 minutes
COOKIE_DOMAIN = "localhost"  # Update to your domain (e.g., example.com)
COOKIE_PATH = "/"
COOKIE_SECURE = False  # Set to True for production (HTTPS)
COOKIE_HTTP_ONLY = False
COOKIE_SAMESITE = "Lax"  # Can be "Lax" or "Strict"

# Register new user
@router.post("/register", response_model=Token)
async def register_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = hash_password(password)
    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        created_date=get_current_timestamp(),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create JWT token
    access_token = create_access_token(data={"sub": new_user.email})
    
    # Set the JWT token in an HTTP-only cookie
    response = JSONResponse(content={"msg": "User registered successfully"})
    response.set_cookie(
        COOKIE_NAME, access_token, max_age=COOKIE_MAX_AGE, expires=COOKIE_MAX_AGE,
        domain=COOKIE_DOMAIN, path=COOKIE_PATH, secure=COOKIE_SECURE, 
        httponly=COOKIE_HTTP_ONLY, samesite=COOKIE_SAMESITE
    )
    return response

# Login user and generate JWT token
@router.post("/login", response_model=Token)
async def login_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == email).first()

    if db_user is None or not verify_password(password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    access_token = create_access_token(data={"sub": db_user.email})
    
    # Set the JWT token in an HTTP-only cookie
    response = JSONResponse(content={"msg": "Login successful"})
    response.set_cookie(
        COOKIE_NAME, access_token, max_age=COOKIE_MAX_AGE, expires=COOKIE_MAX_AGE,
        domain=COOKIE_DOMAIN, path=COOKIE_PATH, secure=COOKIE_SECURE,
        httponly=COOKIE_HTTP_ONLY, samesite=COOKIE_SAMESITE
    )
    return response
