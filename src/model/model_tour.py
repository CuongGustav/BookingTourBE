import uuid
from sqlalchemy import DECIMAL, Column, ForeignKey, Integer, String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.orm import relationship
from src.extension import db


class Tours(db.Model):
    __tablename__ = "tours"

    tour_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tour_code = Column(String(50), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    duration_days = Column(Integer, nullable=False)
    duration_nights = Column(Integer, nullable=False)
    highlights = Column(Text)
    included_services = Column(Text)
    excluded_services = Column(Text)
    attractions = Column(Text)
    cuisine = Column(Text)
    suitable_for = Column(Text)
    ideal_time = Column(String(255))
    transportation = Column(String(255))
    promotions = Column(Text) 
    depart_destination = Column(String(255))
    base_price = Column(DECIMAL(10,2), nullable=False)
    child_price = Column(DECIMAL(10,2))
    infant_price = Column(DECIMAL(10,2))
    single_room_surcharge = Column(DECIMAL(18,2))
    main_image_url = Column(String(500))
    main_image_public_id = Column(String(500))
    rating_average = Column(DECIMAL(3,2), default=0.00)
    total_reviews = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("accounts.account_id"))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    creator = relationship("Accounts")
    images = relationship("Tour_Images", cascade="all, delete", back_populates="tour")
    schedules = relationship("Tour_Schedules", cascade="all, delete", back_populates="tour")
    itineraries = relationship("Tour_Itineraries", cascade="all, delete", back_populates="tour")
    tour_destinations = relationship("Tour_Destinations", cascade="all, delete", back_populates="tour")
    reviews = relationship("Reviews", cascade="all, delete", back_populates="tour")
    bookings = relationship("Bookings", back_populates="tour")
    favorites = relationship("Favorites", back_populates="tour")

    def __init__(self, tour_code, title, duration_days, duration_nights, base_price,
                highlights=None, included_services=None, excluded_services=None, attractions=None,
                 cuisine=None, suitable_for=None, ideal_time=None, transportation=None, promotions=None,
                 child_price=None, infant_price=None, main_image_url=None,depart_destination=None, main_image_public_id =None,
                 created_by=None, is_featured=False, is_active=True, single_room_surcharge=None ):

        self.tour_id = str(uuid.uuid4())
        self.tour_code = tour_code
        self.title = title
        self.duration_days = duration_days
        self.duration_nights = duration_nights
        self.highlights = highlights
        self.included_services = included_services
        self.excluded_services = excluded_services
        self.base_price = base_price
        self.child_price = child_price
        self.infant_price = infant_price
        self.main_image_url = main_image_url
        self.main_image_public_id = main_image_public_id
        self.created_by = created_by
        self.is_featured = is_featured
        self.is_active = is_active
        self.attractions = attractions
        self.cuisine = cuisine
        self.suitable_for = suitable_for
        self.ideal_time = ideal_time
        self.transportation = transportation
        self.promotions = promotions
        self.depart_destination = depart_destination
        self.single_room_surcharge = single_room_surcharge