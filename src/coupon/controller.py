from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.coupon.services import (add_coupon_admin_service,get_all_coupon_admin_service)

coupon = Blueprint("coupon", __name__)

#create coupon
@coupon.route("/admin/add", methods=["POST"])
@jwt_required()
@require_role("qcadmin")
def add_coupon_admin():
    return add_coupon_admin_service()

#get all coupon admin
@coupon.route("/admin/getAll", methods=["GET"])
@jwt_required()
@require_role("qcadmin")
def get_all_coupon_admin():
    return get_all_coupon_admin_service()