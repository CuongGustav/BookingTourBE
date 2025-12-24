from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.model.model_tour import Tours
from src.model.model_favorite import Favorites
from src.marshmallow.library_ma_favorite import favorite_schema
from src.extension import db

#add favorite
def add_favorite_service():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message":"Dữ liệu gửi lên không hợp lệ"}),400
        
        tour_id = data.get("tour_id")
        account_id = get_jwt_identity()

        if not tour_id:
            return jsonify({"message":"Thiếu tour_id"}),400
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message":"Tour không tồn tại"}),400
        
        existing = Favorites.query.filter_by(
            account_id=account_id,
            tour_id=tour_id
        ).first()
        if existing:
            return jsonify({"message": "Tour đã được yêu thích"}), 409
        
        new_favorite = Favorites(
            tour_id=tour_id,
            account_id=account_id
        )
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({"message": "Like tour thành công."}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"lỗi thêm favorite: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Like tour thất bại",
            "error": str(e)
        }), 500

# delete favourite
def delete_favorite_service():
    try:
        data = request.get_json()
        tour_id = data.get("tour_id")
        account_id = get_jwt_identity()


        if not tour_id:
            return jsonify({"message": "Thiếu tour_id"}), 400

        favorite = Favorites.query.filter_by(
            account_id=account_id,
            tour_id=tour_id
        ).first()

        if not favorite:
            return jsonify({"message": "Favorite không tồn tại"}), 404

        db.session.delete(favorite)
        db.session.commit()

        return jsonify({"message": "Unlike tour thành công"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error("Lỗi xoá favorite", exc_info=True)
        return jsonify({
            "message": "Unlike tour thất bại",
            "error": str(e)
        }), 500

#check favorite
def check_favorite_service(tour_id):
    verify_jwt_in_request(optional=True)
    account_id = get_jwt_identity()
    if not account_id:
        return False

    if not tour_id:
        return False
    
    favorite = Favorites.query.filter_by(
        account_id=account_id,
        tour_id=tour_id
    ).first()

    if favorite:
        return True
    else:
        return False