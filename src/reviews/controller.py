from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.reviews.services import (create_review_service, get_all_review_user_service)

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