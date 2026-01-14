from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.reviews.services import create_review_service

reviews = Blueprint("reviews", __name__)

@reviews.route("/create", methods=["POST"])
@jwt_required()
def create_review():
    return create_review_service()