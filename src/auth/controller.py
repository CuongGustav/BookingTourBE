from flask import Blueprint
from src.auth.services import register_account_service

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["POST"])
def register():
    return register_account_service()
