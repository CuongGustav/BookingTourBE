from flask import current_app, jsonify, request
from src.model.model_destination import Destinations
from src.model.model_tour import Tours
from src.model.model_tour_destination import Tour_Destinations
from src.extension import db

# add tour destinations
def create_tour_destination_admin_service ():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message":"Dữ liệu gửi không hợp lệ"}), 400
        
        tour_id = data.get("tour_id")
        destination_ids = data.get("destination_ids")
        if not tour_id or not destination_ids:
            return jsonify({"message": "Thiếu tour_id hoặc destination_ids"}), 400
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message": "Tour không tồn tại"}), 404
        
        for dest_id in destination_ids:
            if not Destinations.query.get(dest_id):
                return jsonify({"message": f"Điểm đến ID {dest_id} không tồn tại"}), 404
            if Tour_Destinations.query.filter_by(tour_id=tour_id, destination_id=dest_id).first():
                continue  
            new_tour_destinations = Tour_Destinations(
                tour_id=tour_id, 
                destination_id=dest_id
            )
            db.session.add(new_tour_destinations)

        db.session.commit()
        return jsonify ({"message": "Thêm tour và các điểm đến thành công",}), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Lỗi thêm tour và các điểm đến: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Thêm tour và các điểm đến thất bại",
            "error": str(e)
        }), 500