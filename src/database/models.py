from sqlalchemy import Column, Integer, String, Boolean, DateTime
from src.database.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_date = Column(DateTime)
    last_logged_in = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    user_type = Column(String, default="user")  # Can be 'admin', 'user', or 'guest'
