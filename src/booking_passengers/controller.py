from flask import Blueprint
from src.booking_passengers.services import (create_booking_passenger_service)

booking_passengers = Blueprint("booking-passengers", __name__)