import uuid
from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Destinations(db.Model):
    __tablename__ = "destinations"

    destination_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    region = Column(String(100))
    description = Column(Text)
    image_url = Column(String(500))
    image_public_id = Column(String(255))
    image_local_path = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    tours = relationship("Tours", back_populates="destination")

    def __init__(self, name, country, region=None, description=None, image_url=None, image_public_id=None, image_local_path=None,is_active=True):
        self.destination_id = str(uuid.uuid4())
        self.name = name
        self.country = country
        self.region = region
        self.description = description
        self.image_url = image_url
        self.image_public_id = image_public_id
        self.image_local_path = image_local_path
        self.is_active = is_active