from flask import jsonify, request
from src.marshmallow.library_ma_tour_itineraries import tour_itinerary_create_schema
from src.model.model_tour_itinerary import Tour_Itineraries
from src.extension import db

# add tour itineraties
def create_tour_itineraties_admin_service ():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message":"Dữ liệu gửi lên không hợp lệ"}),400
       
        tour_id = data.get("tour_id")
        itineraries_data = data.get("itineraries")
        if not tour_id:
            return jsonify({"message":"Thiếu tour_id"})
        if not itineraries_data or len(itineraries_data) == 0:
            return jsonify({"message": "Không có dữ liệu về Lịch trình chi tiết"}), 400
        
        created_itineraries = []
        errors = []

        for idx, item in enumerate(itineraries_data):
            # Validate item 
            errors_item = tour_itinerary_create_schema.validate(item)
            if errors_item:
                errors.append({"index": idx, "errors": errors_item})
                continue

            new_itinerary = Tour_Itineraries(
                tour_id=tour_id,
                title=item.get("title"),
                description=item.get("description"),
                meals=item.get("meals"),
                display_order=item.get("display_order", idx + 1) 
            )
            db.session.add(new_itinerary)
            created_itineraries.append(new_itinerary)

        if errors:
            db.session.rollback()
            return jsonify({"message": "Lỗi xác nhận", "errors": errors}), 400
        
        db.session.commit()
        return jsonify({"message": "Tạo lịch trình chi tiết thành công"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi server: {str(e)}"}), 500