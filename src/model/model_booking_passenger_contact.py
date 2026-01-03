import uuid
from sqlalchemy import TIMESTAMP, Column, ForeignKey, String, Text, func
from src.extension import db
from sqlalchemy.orm import relationship


class BookingPassengerContacts(db.Model):
    __tablename__ = "booking_passenger_contact"

    passenger_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.booking_id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(10), unique=True, nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    booking = relationship("Bookings", back_populates="passenger_contacts")

    def __init__(self, booking_id, full_name, phone=None, address=None):
        self.passenger_id = str(uuid.uuid4())
        self.booking_id = booking_id
        self.full_name = full_name
        self.phone = phone
        self.address = address