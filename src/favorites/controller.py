from flask import Blueprint
from flask_jwt_extended import jwt_required
from src.favorites.services import (add_favorite_service, delete_favorite_service)

favorites = Blueprint("favorites", __name__)

# add favorite
@favorites.route("/add", methods=["POST"])
@jwt_required()
def add_favorite():
    return add_favorite_service()

# delete favorite
@favorites.route("/delete", methods=["DELETE"])
@jwt_required()
def delete_favorite():
    return delete_favorite_service()