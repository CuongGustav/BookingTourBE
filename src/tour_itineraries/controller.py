from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour_itineraries.services import (create_tour_itineraties_admin_service, update_tour_itineraries_by_tour_id_service)

tour_itineraries = Blueprint("tour_itineraries", __name__)

# add tour itineraries
@tour_itineraries.route("/admin/add", methods=["POST"])
@require_role("qcadmin")  
@jwt_required()
def create_tour_itineraries_admin():
    return create_tour_itineraties_admin_service()

# update tour itineraries
@tour_itineraries.route("/admin/update/<string:tour_id>", methods=["PUT"])
@require_role("qcadmin")  
@jwt_required()
def update_tour_itineraries_admin(tour_id):
    return update_tour_itineraries_by_tour_id_service(tour_id)