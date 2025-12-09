from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour.services import(create_tour_admin_service)

tour = Blueprint("tour", __name__)

@tour.route("/admin/add", methods=["POST"])
@jwt_required()  
@require_role("qcadmin")  
def create_tour():
    return create_tour_admin_service()