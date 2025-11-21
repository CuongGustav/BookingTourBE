import uuid
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class PaymentImages(db.Model):
    __tablename__ = "payment_images"

    image_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id = Column(String(36), ForeignKey("payments.payment_id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    uploaded_at = Column(TIMESTAMP, server_default=func.now())

    payment = relationship("Payments", back_populates="payment_images")

    def __init__(self, payment_id, image_url):
        self.image_id = str(uuid.uuid4())
        self.payment_id = payment_id
        self.image_url = image_url