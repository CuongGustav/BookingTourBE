from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.booking.services import (create_booking_service)

booking = Blueprint("booking", __name__)

@booking.route("/create", methods=["POST"])
@jwt_required()
def create_booking():
    return create_booking_service()
