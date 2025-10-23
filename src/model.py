import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from src.extension import db

class ProviderEnum(PyEnum):
    LOCAL = "local"
    GOOGLE = "google"

class User(db.Model):
    __tablename__ = 'users'
    uuid = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=True)
    phone = Column(String(15), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(128), nullable=True)
    date_of_birth = Column(String(50), nullable=True)
    location = Column(String(100), nullable=True)
    google_id = Column(String(100), unique=True, nullable=True)
    provider = Column(Enum(ProviderEnum), default=ProviderEnum.LOCAL, nullable=False)