import uuid
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Tour_Images(db.Model):
    __tablename__ = "tour_images"

    tour_image_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_id = Column(String(36), ForeignKey("tours.tour_id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_public_id = Column(String(500), nullable=False)
    image_local_path = Column(String(500), nullable=False)
    display_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    tour = relationship("Tours", back_populates="images")

    def __init__(self, tour_id, image_url, image_public_id, image_local_path,  display_order=0):
        self.tour_image_id = str(uuid.uuid4())
        self.tour_id = tour_id
        self.image_url = image_url
        self.image_public_id = image_public_id
        self.image_local_path = image_local_path
        self.display_order = display_order