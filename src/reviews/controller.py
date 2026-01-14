from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.common.decorators import require_role
from src.reviews.services import (create_review_service, get_all_review_user_service, delete_review_service, 
                                  read_detail_review_service, update_review_service, get_all_review_admin_service,
                                  read_detail_review_admin_service)

reviews = Blueprint("reviews", __name__)

#create review
@reviews.route("/create", methods=["POST"])
@jwt_required()
def create_review():
    return create_review_service()

#get all review user
@reviews.route("/all", methods=["GET"])
@jwt_required()
def get_all_review_user():
    return get_all_review_user_service()

#delete review
@reviews.route("/delete/<review_id>", methods=["DELETE"])
@jwt_required()
def delete_review(review_id):
    return delete_review_service(review_id)

#read detail review user
@reviews.route("/<review_id>", methods=["GET"])
@jwt_required()
def read_detail_review(review_id):
    return read_detail_review_service(review_id)

#update review user
@reviews.route("/update/<review_id>", methods=["PATCH"])
@jwt_required()
def update_review(review_id):
    return update_review_service(review_id)

#get all review admin
@reviews.route("/admin/all", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def get_all_review_admin():
    return get_all_review_admin_service()

#get detail review admin
@reviews.route("/admin/<review_id>", methods=["GET"])
@jwt_required()
@require_role('qcadmin')
def read_detail_review_admin(review_id):
    return read_detail_review_admin_service(review_id)