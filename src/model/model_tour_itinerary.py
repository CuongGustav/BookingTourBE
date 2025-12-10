# src/models/model_tour_itinerary.py
import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Tour_Itineraries(db.Model):
    __tablename__ = "tour_itineraries"

    itinerary_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_id = Column(String(36), ForeignKey("tours.tour_id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    meals = Column(String(255))
    display_order = Column(Integer, default=1, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    tour = relationship("Tours", back_populates="itineraries")

    def __init__(self,tour_id: str,title: str,description = None,meals = None,display_order = None):
        self.itinerary_id = str(uuid.uuid4())
        self.tour_id = tour_id
        self.title = title
        self.description = description
        self.meals = meals
        self.display_order = display_order