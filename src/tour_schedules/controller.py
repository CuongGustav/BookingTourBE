from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour_schedules.services import (create_tour_schedules_admin_service)

tour_schedules = Blueprint("tour_schedules", __name__)

# add tour itineraries
@tour_schedules.route("/admin/add", methods=["POST"])
@require_role("qcadmin")  
@jwt_required()
def create_tour_itineraries_admin():
    return create_tour_schedules_admin_service()