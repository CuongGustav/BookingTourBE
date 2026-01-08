from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.booking.services import (create_booking_service, get_bookings_user_service, get_booking_by_id_service, cancel_booking_service)

booking = Blueprint("booking", __name__)

@booking.route("/create", methods=["POST"])
@jwt_required()
def create_booking():
    return create_booking_service()

@booking.route("/all", methods=["GET"])
@jwt_required()
def get_bookings_user():
    return get_bookings_user_service()

@booking.route("/<string:booking_id>", methods=["GET"]) 
@jwt_required()
def get_booking_by_id(booking_id):
    return get_booking_by_id_service(booking_id)

@booking.route("/cancel/<string:booking_id>", methods=["PATCH"]) 
@jwt_required()
def cancel_booking(booking_id):
    return cancel_booking_service(booking_id)
