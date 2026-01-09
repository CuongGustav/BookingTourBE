from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.booking.services import (create_booking_service, get_bookings_user_service, get_booking_by_id_service, cancel_booking_service, 
                                  update_booking_service, get_all_booking_admin_service)
from src.common.decorators import require_role

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

@booking.route("/update", methods=["PATCH"])
@jwt_required()
def update_booking():
    return update_booking_service()

@booking.route("/admin/all", methods=["GET"])
@jwt_required()
@require_role("qcadmin")
def get_all_booking_admin():
    return get_all_booking_admin_service()
