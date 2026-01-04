from flask import Blueprint
from src.booking.services import (create_tour_service)

booking = Blueprint("booking", __name__)

