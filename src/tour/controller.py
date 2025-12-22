from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.tour.services import(create_tour_admin_service, get_all_tour_service, get_all_tour_admin_service, get_8_tour_service,
                             filter_tours_service, get_tour_detail_service)

tour = Blueprint("tour", __name__)

@tour.route("/admin/add", methods=["POST"])
@jwt_required()  
@require_role("qcadmin")  
def create_tour():
    return create_tour_admin_service()

@tour.route("/admin/all", methods=["GET"])
@jwt_required()  
@require_role("qcadmin")  
def get_all_tour_admin():
    return get_all_tour_admin_service()

@tour.route("/all", methods=["GET"])
def get_all_tour():
    return get_all_tour_service()

@tour.route("/8tour", methods=["GET"])
def get_8_tour():
    return get_8_tour_service()

@tour.route("/filterTour", methods=["POST"])
def filter_tours():
    return filter_tours_service()

@tour.route("/<string:tour_id>", methods=["GET"])
def get_tour_detail(tour_id):
    return get_tour_detail_service(tour_id)