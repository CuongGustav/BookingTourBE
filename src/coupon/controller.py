from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.coupon.services import add_coupon_admin_service

coupons = Blueprint("coupons", __name__)

#create coupon
@coupons.route("/admin/add", methods=["POST"])
@jwt_required()
@require_role('qcadmin')
def add_coupon_admin():
    return add_coupon_admin_service()