import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DECIMAL, Integer, Boolean, DateTime, TIMESTAMP, Text, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from src.extension import db


class DiscountTypeEnum(PyEnum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Coupons(db.Model):
    __tablename__ = "coupons"

    coupon_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    discount_type = Column(
        SAEnum(DiscountTypeEnum, values_callable=lambda obj: [e.value for e in obj], native_enum=False),
        nullable=False
    )
    discount_value = Column(DECIMAL(10,2), nullable=False)
    min_order_amount = Column(DECIMAL(10,2), default=0)
    max_discount_amount = Column(DECIMAL(10,2))
    usage_limit = Column(Integer)
    used_count = Column(Integer, default=0)
    valid_from = Column(DateTime, nullable=False)
    valid_to = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("accounts.account_id"))
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    image_coupon_url = Column(String(255))
    image_coupon_public_id = Column(String(255))

    creator = relationship("Accounts", back_populates="created_coupons")
    bookings = relationship("Bookings", back_populates="coupon")

    def __init__(self, code, discount_type, discount_value,
                 valid_from, valid_to, description=None,
                 min_order_amount=0, max_discount_amount=None,
                 usage_limit=None, created_by=None, is_active=True,
                 image_coupon_url=None, image_coupon_public_id=None ):
        self.coupon_id = str(uuid.uuid4())
        self.code = code
        self.description = description
        self.discount_type = discount_type
        self.discount_value = discount_value
        self.min_order_amount = min_order_amount
        self.max_discount_amount = max_discount_amount
        self.usage_limit = usage_limit
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.created_by = created_by
        self.is_active = is_active
        self.image_coupon_url = image_coupon_url
        self.image_coupon_public_id = image_coupon_public_id