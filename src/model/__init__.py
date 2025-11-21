# src/model/__init__.py
from .model_account import Accounts
from .model_booking import Bookings
from .model_coupon import Coupons
from .model_destination import Destinations
from .model_tour import Tours
from .model_tour_schedule import TourSchedules
from .model_booking_passenger import BookingPassengers
from .model_favorite import Favorites
from .model_tour_image import TourImages
from .model_payment import Payments
from .model_payment_image import PaymentImages
from .model_review import Reviews
from .model_review_image import ReviewImages

__all__ = [
    "Accounts", "Bookings", "Coupons", "Destinations",
    "Tours", "TourSchedules", "BookingPassengers", "Favorites",
    "TourImages", "Payments", "PaymentImages", "Reviews", "ReviewImages"
]