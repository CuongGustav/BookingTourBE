from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.account.services import (get_all_information_account_service, change_password_service)

account = Blueprint("account", __name__)

@account.route("/information", methods=["GET"])
def get_all_information_account():
    return get_all_information_account_service()

@account.route("/changepassword", methods=["POST"])
def change_password():
    return change_password_service()