from flask import Blueprint
from src.auth.services import (register_account_service, login_account_user_service, get_current_user_service, 
                               logout_account_user_service, refresh_token_service)

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["POST"])
def register():
    return register_account_service()

@auth.route("/login", methods=["POST"])
def login():
    return login_account_user_service()

@auth.route("/whoami", methods=["GET"])
def get_current_user():
    return get_current_user_service()

@auth.route("/logout", methods=["POST"])
def logout_account_user():
    return logout_account_user_service()

@auth.route("/refresh", methods=["POST"])
def refresh_token():
    return refresh_token_service()