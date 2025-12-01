from flask import Blueprint
from src.destination.services import (get_cloudinary_usage_service, add_destination_service)

destination = Blueprint("destination", __name__)

@destination.route("/cloudinary_usage", methods=["GET"])
def get_cloudinary_usage():
    return get_cloudinary_usage_service()

@destination.route("/admin/add", methods=["POST"])
def add_destination():
    return add_destination_service()