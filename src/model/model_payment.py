import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DECIMAL, TIMESTAMP, Text, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.extension import db


class PaymentMethodEnum(PyEnum):
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    QR_CODE = "qr_code"


class PaymentStatusEnum(PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payments(db.Model):
    __tablename__ = "payments"

    payment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    booking_id = Column(String(36), ForeignKey("bookings.booking_id"), nullable=False)
    payment_method = Column(
        SAEnum(PaymentMethodEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        nullable=False
    )
    qr_code_url = Column(String(500))
    amount = Column(DECIMAL(10,2), nullable=False)
    status = Column(
        SAEnum(PaymentStatusEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        default=PaymentStatusEnum.PENDING.value,
        nullable=False
    )
    payment_date = Column(TIMESTAMP)
    note_payment = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    booking = relationship("Bookings", back_populates="payments")
    payment_images = relationship("PaymentImages", cascade="all, delete", back_populates="payment")

    def __init__(self, booking_id, payment_method, amount, status=PaymentStatusEnum.PENDING.value,
                 qr_code_url=None, payment_date=None, note_payment=None):
        self.payment_id = str(uuid.uuid4())
        self.booking_id = booking_id
        self.payment_method = payment_method
        self.amount = amount
        self.status = status
        self.qr_code_url = qr_code_url
        self.payment_date = payment_date
        self.note_payment = note_payment