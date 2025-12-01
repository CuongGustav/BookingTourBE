from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.account.services import (get_all_information_account_service, change_password_service, update_information_account_service,
                                  get_all_account_service, get_account_by_uuid_admin_service, update_account_admin_service,
                                  delete_soft_account_admin_service, delete_soft_account_user_service)

account = Blueprint("account", __name__)

@account.route("/information", methods=["GET"])
def get_all_information_account():
    return get_all_information_account_service()

@account.route("/changepassword", methods=["POST"])
def change_password():
    return change_password_service()

@account.route("/update", methods=["PUT"])
def update_information_account():
    return update_information_account_service()

@account.route("/delete_soft", methods=["PUT"])
def delete_account():
    return delete_soft_account_user_service()

@account.route("/admin/allaccount", methods=["GET"])
def get_all_account():
    return get_all_account_service()

@account.route("/admin/<string:account_id>", methods=["GET"])
def get_account_by_account_id_admin(account_id):
    return get_account_by_uuid_admin_service(account_id)

@account.route("/admin/update", methods=["PUT"])
def update_account_admin():
    return update_account_admin_service()

@account.route("/admin/delete_soft", methods=["PUT"])
def delete_soft_account_admin():
    return delete_soft_account_admin_service()