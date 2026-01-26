import uuid
from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, String, Integer, DECIMAL, TIMESTAMP, Text, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.extension import db


class BookingStatusEnum(PyEnum):
    PENDING = "pending"
    PAID = "paid"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CANCEL_PENDING = "cancel_pending"
    DEPOSIT = "deposit"


class Bookings(db.Model):
    __tablename__ = "bookings"

    booking_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_code = Column(String(50), unique=True, nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.account_id"), nullable=False)
    tour_id = Column(String(36), ForeignKey("tours.tour_id"), nullable=False)
    schedule_id = Column(String(36), ForeignKey("tour_schedules.schedule_id"), nullable=False)
    coupon_id = Column(String(36), ForeignKey("coupons.coupon_id"), nullable=True)
    num_adults = Column(Integer, default=1, nullable=False)
    num_children = Column(Integer, default=0)
    num_infants = Column(Integer, default=0)
    total_price = Column(DECIMAL(10,2), nullable=False)
    discount_amount = Column(DECIMAL(10,2), default=0)
    final_price = Column(DECIMAL(10,2), nullable=False)
    paid_money = Column(DECIMAL(10,2), nullable=False)
    is_full_payment = Column(Boolean, default=False)
    remaining_amount = Column(DECIMAL(10,2), default=0)
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(10), nullable=False)
    contact_address = Column(String(255), nullable=False)
    special_request = Column(Text)
    # SAEnum dùng để mapping Python Enum với cột trong database
    status = Column(
        SAEnum(BookingStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        default=BookingStatusEnum.PENDING.value,
        nullable=False
    )
    cancellation_reason = Column(Text)
    cancelled_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # back_populates để thiết lập quan hệ hai chiều, cho phép truy vấn ngươc lại từ bảng liên quan
    account = relationship("Accounts", back_populates="bookings")
    tour = relationship("Tours", back_populates="bookings")
    schedule = relationship("Tour_Schedules", back_populates="bookings")
    coupon = relationship("Coupons", back_populates="bookings")
    passengers = relationship("BookingPassengers", cascade="all, delete", back_populates="booking")
    payments = relationship("Payments", cascade="all, delete", back_populates="booking")
    reviews = relationship("Reviews", cascade="all, delete", back_populates="booking")

    def __init__(self, booking_code, account_id, tour_id, schedule_id,
                 total_price, final_price, contact_name, contact_email, contact_phone, contact_address,
                 num_adults=1, num_children=0, num_infants=0, remaining_amount=0, is_full_payment=False,
                 coupon_id=None, discount_amount=0, special_request=None, paid_money=0,
                 status=BookingStatusEnum.PENDING.value, cancellation_reason=None, cancelled_at=None):
        self.booking_id = str(uuid.uuid4())
        self.booking_code = booking_code
        self.account_id = account_id
        self.tour_id = tour_id
        self.schedule_id = schedule_id
        self.coupon_id = coupon_id
        self.num_adults = num_adults
        self.num_children = num_children
        self.num_infants = num_infants
        self.total_price = total_price
        self.discount_amount = discount_amount
        self.final_price = final_price
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.contact_address = contact_address
        self.special_request = special_request
        self.status = status
        self.cancellation_reason = cancellation_reason
        self.cancelled_at = cancelled_at
        self.paid_money = paid_money
        self.remaining_amount = remaining_amount
        self.is_full_payment = is_full_payment