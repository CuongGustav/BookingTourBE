from flask import Blueprint
from src.booking_passenger_contacts.services import (create_booking_passenger_contact_service)

booking_passenger_contact = Blueprint("booking-passenger-contact", __name__)