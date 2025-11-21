import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DECIMAL, Date, TIMESTAMP, func, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.extension import db


class ScheduleStatusEnum(PyEnum):
    AVAILABLE = "available"
    FULL = "full"
    CANCELLED = "cancelled"


class TourSchedules(db.Model):
    __tablename__ = "tour_schedules"

    schedule_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_id = Column(String(36), ForeignKey("tours.tour_id"), nullable=False)
    departure_date = Column(Date, nullable=False)
    return_date = Column(Date, nullable=False)
    available_seats = Column(Integer, nullable=False)
    booked_seats = Column(Integer, default=0)
    price_adult = Column(DECIMAL(10,2), nullable=False)
    price_child = Column(DECIMAL(10,2))
    price_infant = Column(DECIMAL(10,2))
    status = Column(
        SAEnum(ScheduleStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        default=ScheduleStatusEnum.AVAILABLE.value,
        nullable=False
    )
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    tour = relationship("Tours", back_populates="schedules")
    bookings = relationship("Bookings", back_populates="schedule")

    def __init__(self, tour_id, departure_date, return_date, available_seats,
                 price_adult, price_child=None, price_infant=None, status=ScheduleStatusEnum.AVAILABLE.value):
        self.schedule_id = str(uuid.uuid4())
        self.tour_id = tour_id
        self.departure_date = departure_date
        self.return_date = return_date
        self.available_seats = available_seats
        self.price_adult = price_adult
        self.price_child = price_child
        self.price_infant = price_infant
        self.status = status