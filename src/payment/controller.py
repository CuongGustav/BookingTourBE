from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.payment.services import (create_payment_service, generate_qr_code_service, get_all_payment_admin_service, 
                                  create_payment_admin_service, read_payment_detail_admin_service, 
                                  read_payment_detail_admin_by_booking_id_service, create_payment_remaining_admin_service,
                                  create_payment_remaining_user_service)

payment = Blueprint("payment", __name__)

@payment.route("/create", methods=["POST"])
@jwt_required()
def create_payment():
    return create_payment_service()

@payment.route("/generate-qr/<booking_id>", methods=["GET"])
@jwt_required()
def generate_qr(booking_id):
    return generate_qr_code_service(booking_id)

@payment.route("/admin/all", methods=["GET"])
@jwt_required()
@require_role("qcadmin")  
def get_all_payment_admin():
    return get_all_payment_admin_service()

@payment.route("/admin/create", methods=["POST"])
@jwt_required()
@require_role("qcadmin")
def create_payment_admin():
    return create_payment_admin_service()

@payment.route("/admin/<payment_id>", methods=["GET"])
@jwt_required()
@require_role("qcadmin")
def read_payment_detail_admin(payment_id):
    return read_payment_detail_admin_service(payment_id)

@payment.route("/admin/booking/<booking_id>", methods=["GET"])
@jwt_required()
@require_role("qcadmin")
def read_payment_detail_admin_by_booking_id(booking_id):
    return read_payment_detail_admin_by_booking_id_service(booking_id)

@payment.route("/admin/create-remaining", methods=["POST"])
@jwt_required()
@require_role("qcadmin")
def create_payment_remaining_admin():
    return create_payment_remaining_admin_service()

@payment.route("/create-remaining", methods=["POST"])
@jwt_required()
def create_payment_remaining_user():
    return create_payment_remaining_user_service()