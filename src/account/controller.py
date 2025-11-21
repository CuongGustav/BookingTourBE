from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.account.services import (get_all_information_account_service)

account = Blueprint("account", __name__)

@account.route("/information", methods=["GET"])
def get_all_information_account():
    return get_all_information_account_service()