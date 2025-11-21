import uuid
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, func, Text
from sqlalchemy.orm import relationship
from src.extension import db


class Reviews(db.Model):
    __tablename__ = "reviews"

    review_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_id = Column(String(36), ForeignKey("tours.tour_id"), nullable=False)
    booking_id = Column(String(36), ForeignKey("bookings.booking_id"), nullable=False)
    account_id = Column(String(36), ForeignKey("accounts.account_id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    is_verified_booking = Column(Boolean, default=True)
    admin_reply = Column(Text)
    admin_reply_by = Column(String(36), ForeignKey("accounts.account_id"))
    admin_replied_at = Column(TIMESTAMP)
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tour = relationship("Tours", back_populates="reviews")
    booking = relationship("Bookings", back_populates="reviews")
    account = relationship("Accounts", back_populates="reviews", foreign_keys="Reviews.account_id")
    admin = relationship("Accounts", back_populates="admin_replies", foreign_keys="Reviews.admin_reply_by")
    review_images = relationship("ReviewImages", cascade="all, delete", back_populates="review")

    def __init__(self, tour_id, booking_id, account_id, rating, comment,
                 is_verified_booking=True, admin_reply=None, admin_reply_by=None,
                 admin_replied_at=None, is_approved=False, is_active=True):
        self.review_id = str(uuid.uuid4())
        self.tour_id = tour_id
        self.booking_id = booking_id
        self.account_id = account_id
        self.rating = rating
        self.comment = comment
        self.is_verified_booking = is_verified_booking
        self.admin_reply = admin_reply
        self.admin_reply_by = admin_reply_by
        self.admin_replied_at = admin_replied_at
        self.is_approved = is_approved
        self.is_active = is_active