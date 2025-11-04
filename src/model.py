import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Enum as SAEnum, Date, Text, Boolean, TIMESTAMP, func
from src.extension import db
from werkzeug.security import generate_password_hash, check_password_hash

# Enum
class GenderEnum(PyEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
class RoleEnum(PyEnum):
    QCUSER = "qcuser"
    QCADMIN = "qcadmin"
class ProviderEnum(PyEnum):
    LOCAL = "local"
    GOOGLE = "google"

# Accounts
class Accounts(db.Model):
    __tablename__ = 'accounts'

    account_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    google_id = Column(String(255), nullable=True)
    # provider so that SQLAlchemy maps the string itself
    provider = Column(
        SAEnum(ProviderEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        default=ProviderEnum.LOCAL.value,
        nullable=True
    )
    phone = Column(String(10), nullable=True)
    gender = Column(
        SAEnum(GenderEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        nullable=True
    )
    role_account = Column(
        SAEnum(RoleEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        default=RoleEnum.QCUSER.value,
        nullable=False
    )
    date_of_birth = Column(Date, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __init__(self, email, password_hash, full_name, google_id=None, provider="local", phone=None,
                 date_of_birth=None, gender=None, address=None, role_account="qcuser", is_active=True):
        self.account_id = str(uuid.uuid4())
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.google_id = google_id
        self.provider = provider
        self.phone = phone
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.address = address
        self.role_account = role_account
        self.is_active = is_active
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
