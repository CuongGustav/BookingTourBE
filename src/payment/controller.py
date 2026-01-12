from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.payment.services import create_payment_service, generate_qr_code_service

payment = Blueprint("payment", __name__)

@payment.route("/create", methods=["POST"])
@jwt_required()
def create_payment():
    return create_payment_service()

@payment.route("/generate-qr/<booking_id>", methods=["GET"])
@jwt_required()
def generate_qr(booking_id):
    return generate_qr_code_service(booking_id)