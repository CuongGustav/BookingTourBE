from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour_destinations.services import (create_tour_destination_admin_service, update_tour_destination_admin_service)

tour_destinations = Blueprint("tour_destinations", __name__)

@tour_destinations.route("/admin/add", methods=["POST"])
@require_role("qcadmin")  
@jwt_required()
def create_tour_destination_admin():
    return create_tour_destination_admin_service()

@tour_destinations.route("/admin/update/<string:tour_id>", methods=["PUT"])
@require_role("qcadmin")  
@jwt_required()
def update_tour_destination_admin(tour_id):
    return update_tour_destination_admin_service(tour_id)