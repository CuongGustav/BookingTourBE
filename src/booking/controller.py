from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required
from src.booking.services import (create_booking_service, get_bookings_user_service, get_booking_by_id_service, cancel_booking_service, 
                                  update_booking_service, get_all_booking_admin_service, read_booking_detail_admin_service, 
                                  cancel_booking_pending_admin_service, cancel_booking_paid_admin_service, confirm_booking_paid_admin_service,
                                  cancel_booking_confirmed_user_service, cancel_booking_confirm_and_refund_payment_admin_service,
                                  confirm_booking_cancel_pending_and_refund_payment_admin_service, cancel_booking_cancel_pending_admin_service,
                                  cancel_booking_deposit_admin_service, confirm_booking_deposit_admin_service)
from src.common.decorators import require_role
from src.update_status_completed_booking import update_completed_bookings

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

#update booking user
@booking.route("/update", methods=["PATCH"])
@jwt_required()
def update_booking():
    return update_booking_service()

#read all booking admin
@booking.route("/admin/all", methods=["GET"])
@jwt_required()
@require_role("qcadmin")
def get_all_booking_admin():
    return get_all_booking_admin_service()

#read booking detail admin
@booking.route("/admin/<string:booking_id>", methods=["GET"])
@jwt_required()
@require_role("qcadmin")
def read_booking_detail_admin(booking_id):
    return read_booking_detail_admin_service(booking_id)

#cancel booking pending admin
@booking.route("/admin/cancel-booking-pending/<string:booking_id>", methods=["PATCH"])
@jwt_required()
@require_role("qcadmin")
def cancel_booking_pending_admin(booking_id):
    return cancel_booking_pending_admin_service(booking_id)

#cancel booking paid admin
@booking.route("/admin/cancel-booking-paid/<string:booking_id>", methods=["PATCH"])
@jwt_required()
@require_role("qcadmin")
def cancel_booking_paid_admin(booking_id):
    return cancel_booking_paid_admin_service(booking_id)

#confirm booking paid admin
@booking.route("/admin/confirm-booking-paid/<string:booking_id>", methods=["PATCH"])
@jwt_required()
@require_role("qcadmin")
def confirm_booking_paid_admin(booking_id):
    return confirm_booking_paid_admin_service(booking_id)

#cancel booking confirm user
@booking.route("/cancel-booking-confirm/<string:booking_id>", methods=["PATCH"])
@jwt_required()
def cancel_booking_confirmed_user(booking_id):
    return cancel_booking_confirmed_user_service(booking_id)

#cancel booking confirm admin
@booking.route("/admin/cancel-and-refund/<booking_id>", methods=["PATCH"])
@jwt_required()
@require_role("qcadmin")
def cancel_booking_confirm_and_refund_payment_admin(booking_id):
    return cancel_booking_confirm_and_refund_payment_admin_service(booking_id)

#confirm booking cancel pending admin
@booking.route("/admin/confirm-booking-cancel-pending-and-refund/<booking_id>", methods=["PATCH"])
@jwt_required()
@require_role("qcadmin")
def confirm_booking_cancel_pending_and_refund_payment_admin(booking_id):
    return confirm_booking_cancel_pending_and_refund_payment_admin_service(booking_id)

#cancel booking cancel pending
@booking.route("/admin/cancel-booking-cancel-pending/<booking_id>", methods=["PATCH"])
@jwt_required()
@require_role("qcadmin")
def cancel_booking_cancel_pending_admin(booking_id):
    return cancel_booking_cancel_pending_admin_service(booking_id)

#cancel booking deposit admin
@booking.route("/admin/cancel-booking-deposit/<booking_id>", methods=["PUT"])
@jwt_required()
@require_role("qcadmin")
def cancel_booking_deposit_admin(booking_id):
    return cancel_booking_deposit_admin_service(booking_id)

#confirm booking deposit admin
@booking.route("/admin/confirm-booking-deposit/<booking_id>", methods=["PUT"])
@jwt_required()
@require_role("qcadmin")
def confirm_booking_deposit_admin(booking_id):
    return confirm_booking_deposit_admin_service(booking_id)

#update status completed booking
@booking.route("/admin/test-complete-bookings", methods=["POST"])
@jwt_required()
@require_role("qcadmin")
def test_complete_bookings():
    update_completed_bookings(current_app._get_current_object())
    return jsonify({"message": "Đã chạy job cập nhật booking"}), 200