import uuid
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class ReviewImages(db.Model):
    __tablename__ = "review_images"

    image_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    review_id = Column(String(36), ForeignKey("reviews.review_id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    review = relationship("Reviews", back_populates="review_images")

    def __init__(self, review_id, image_url):
        self.image_id = str(uuid.uuid4())
        self.review_id = review_id
        self.image_url = image_url