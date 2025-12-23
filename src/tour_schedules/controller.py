from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour_schedules.services import (create_tour_schedules_admin_service, update_tour_schedule_service)

tour_schedules = Blueprint("tour_schedules", __name__)

# add tour itineraries
@tour_schedules.route("/admin/add", methods=["POST"])
@require_role("qcadmin")  
@jwt_required()
def create_tour_schedules_admin():
    return create_tour_schedules_admin_service()

# update tour itineraries
@tour_schedules.route("/admin/update/<string:tour_id>", methods=["PUT"])
@require_role("qcadmin")  
@jwt_required()
def update_tour_schedules_admin(tour_id):
    return update_tour_schedule_service(tour_id)