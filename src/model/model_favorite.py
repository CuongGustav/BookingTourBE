import uuid
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Favorites(db.Model):
    __tablename__ = "favorites"

    favorite_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(36), ForeignKey("accounts.account_id"), nullable=False)
    tour_id = Column(String(36), ForeignKey("tours.tour_id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    account = relationship("Accounts", back_populates="favorites")
    tour = relationship("Tours", back_populates="favorites")

    def __init__(self, account_id, tour_id):
        self.favorite_id = str(uuid.uuid4())
        self.account_id = account_id
        self.tour_id = tour_id