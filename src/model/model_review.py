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
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tour = relationship("Tours", back_populates="reviews")
    booking = relationship("Bookings", back_populates="reviews")
    account = relationship("Accounts", back_populates="reviews", foreign_keys="Reviews.account_id")
    review_images = relationship("ReviewImages", cascade="all, delete", back_populates="review")

    def __init__(self, tour_id, booking_id, account_id, rating, comment):
        self.review_id = str(uuid.uuid4())
        self.tour_id = tour_id
        self.booking_id = booking_id
        self.account_id = account_id
        self.rating = rating
        self.comment = comment