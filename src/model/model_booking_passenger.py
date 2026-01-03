import uuid
from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, String, ForeignKey, Date, TIMESTAMP, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.extension import db


class PassengerTypeEnum(PyEnum):
    ADULT = "adult"
    CHILD = "child"
    INFANT = "infant"


class GenderEnum(PyEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BookingPassengers(db.Model):
    __tablename__ = "booking_passengers"

    passenger_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.booking_id"), nullable=False)
    passenger_type = Column(
        SAEnum(PassengerTypeEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        nullable=False
    )
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(
        SAEnum(GenderEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        nullable=True
    )
    id_number = Column(String(50))
    single_room = Column(Boolean, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    booking = relationship("Bookings", back_populates="passengers")

    def __init__(self, booking_id, passenger_type, full_name, single_room=None,
                 date_of_birth=None, gender=None, id_number=None):
        self.passenger_id = str(uuid.uuid4())
        self.booking_id = booking_id
        self.passenger_type = passenger_type
        self.full_name = full_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.id_number = id_number
        self.single_room = single_room