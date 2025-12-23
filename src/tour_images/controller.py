from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour_images.services import (create_tour_images_admin_service, update_tour_images_admin_service)

tour_images = Blueprint("tour_images", __name__, url_prefix="/tour_images")

@tour_images.route("/admin/add", methods=["POST"])
@require_role("qcadmin")
@jwt_required()
def add_tour_images_admin():
    return create_tour_images_admin_service()

@tour_images.route("/admin/update/<string:tour_id>", methods=["PUT"])
@require_role("qcadmin")
@jwt_required()
def update_tour_images_admin(tour_id):
    return update_tour_images_admin_service(tour_id)