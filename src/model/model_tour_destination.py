import uuid
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Tour_Destinations(db.Model):
    __tablename__ = "tour_destinations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_id = Column(String(36), ForeignKey("tours.tour_id"), nullable=False)
    destination_id = Column(String(36), ForeignKey("destinations.destination_id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    tour = relationship("Tours", back_populates="tour_destinations")
    destination = relationship("Destinations", back_populates="tour_destinations")

    def __init__(self, tour_id, destination_id):
        self.id = str(uuid.uuid4())
        self.tour_id = tour_id  
        self.destination_id = destination_id