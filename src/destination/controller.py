from flask import Blueprint
from src.destination.services import (get_cloudinary_usage_service, add_destination_service, get_all_destination_admin_service,
                                      get_destination_by_uuid_admin_service, update_destination_admin_service,
                                      delete_destination_admin_service, get_all_destination_by_region_service)

destination = Blueprint("destination", __name__)

@destination.route("/cloudinary_usage", methods=["GET"])
def get_cloudinary_usage():
    return get_cloudinary_usage_service()

@destination.route("/admin/add", methods=["POST"])
def add_destination():
    return add_destination_service()

@destination.route("/admin/all", methods=["GET"])
def get_all_destination():
    return get_all_destination_admin_service()

@destination.route("/admin/<string:destination_id>", methods=["GET"])
def get_destination_by_uuid(destination_id):
    return get_destination_by_uuid_admin_service(destination_id)

#update destination admin
@destination.route("/admin/update/<string:destination_id>", methods=["PUT"])
def update_destination_admin(destination_id):
    return update_destination_admin_service(destination_id)

#delete destination admin
@destination.route("/admin/delete/<string:destination_id>", methods=["DELETE"])
def delete_destination_admin(destination_id):
    return delete_destination_admin_service(destination_id)

#get all destination by region guest
@destination.route("/allByRegion", methods=["GET"])
def get_all_destination_by_region():
    return get_all_destination_by_region_service()