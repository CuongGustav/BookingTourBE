import uuid
from sqlalchemy import DECIMAL, Column, ForeignKey, Integer, String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Tours(db.Model):
    __tablename__ = "tours"

    tour_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_code = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    slug = Column(String(255), unique=True)
    destination_id = Column(String(36), ForeignKey("destinations.destination_id"))
    duration_days = Column(Integer, nullable=False)
    duration_nights = Column(Integer, nullable=False)
    description = Column(Text)
    highlights = Column(Text)
    itinerary = Column(Text)
    included_services = Column(Text)
    excluded_services = Column(Text)
    terms_conditions = Column(Text)
    base_price = Column(DECIMAL(10,2), nullable=False)
    child_price = Column(DECIMAL(10,2))
    infant_price = Column(DECIMAL(10,2))
    main_image = Column(String(500))
    rating_average = Column(DECIMAL(3,2), default=0.00)
    total_reviews = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("accounts.account_id"))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    destination = relationship("Destinations", back_populates="tours")
    creator = relationship("Accounts")
    images = relationship("TourImages", cascade="all, delete", back_populates="tour")
    schedules = relationship("TourSchedules", cascade="all, delete", back_populates="tour")
    reviews = relationship("Reviews", cascade="all, delete", back_populates="tour")
    bookings = relationship("Bookings", back_populates="tour")
    favorites = relationship("Favorites", back_populates="tour")

    def __init__(self, tour_code, title, destination_id, duration_days, duration_nights, base_price,
                 slug=None, description=None, highlights=None, itinerary=None,
                 included_services=None, excluded_services=None, terms_conditions=None,
                 child_price=None, infant_price=None, main_image=None,
                 created_by=None, is_featured=False, is_active=True):

        self.tour_id = str(uuid.uuid4())
        self.tour_code = tour_code
        self.title = title
        self.slug = slug
        self.destination_id = destination_id
        self.duration_days = duration_days
        self.duration_nights = duration_nights
        self.description = description
        self.highlights = highlights
        self.itinerary = itinerary
        self.included_services = included_services
        self.excluded_services = excluded_services
        self.terms_conditions = terms_conditions
        self.base_price = base_price
        self.child_price = child_price
        self.infant_price = infant_price
        self.main_image = main_image
        self.created_by = created_by
        self.is_featured = is_featured
        self.is_active = is_active