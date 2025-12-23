from flask import jsonify, request
from src.marshmallow.library_ma_tour_itineraries import tour_itinerary_create_schema, tour_itineraries_read_schema
from src.model.model_tour import Tours
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
    
#get tour details by tour id
def get_tour_itineraries_by_tour_id_service(tour_id):
    if not tour_id:
        return jsonify({"message": "Thiếu tour_id"}), 400
    try:
        itineraries = Tour_Itineraries.query.filter_by(tour_id=tour_id).order_by(Tour_Itineraries.display_order).all()
        
        if not itineraries:
            return []
        
        result = tour_itineraries_read_schema.dump(itineraries)
        return result
    except Exception as e:
        print(f"[TourSchedulesService] Lỗi ở hàm get_tour_schedule_service {tour_id}: {str(e)}")
        db.session.rollback()
        return []
    
#update tour itineraries by tour id
def update_tour_itineraries_by_tour_id_service(tour_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message":"Dữ liệu gửi lên không hợp lệ"}),400
        
        itineraries_data = data.get("itineraries")
        if not tour_id:
            return jsonify({"message":"Thiếu tour_id"})
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message": "Tour không tồn tại"}), 404
        if not itineraries_data or len(itineraries_data) == 0:
            return jsonify({"message": "Không có dữ liệu về Lịch trình chi tiết"}), 400
        
        existing_itineraries = Tour_Itineraries.query.filter_by(tour_id=tour_id).all()
        existing_ids = {itinerary.itinerary_id for itinerary in existing_itineraries}
        
        updated_ids = set()
        errors = []

        for idx, item in enumerate(itineraries_data):
            errors_item = tour_itinerary_create_schema.validate(item)
            if errors_item:
                errors.append({"index": idx, "errors": errors_item})
                continue

            itinerary_id = item.get("itinerary_id")
            if itinerary_id and itinerary_id in existing_ids:
                itinerary = Tour_Itineraries.query.get(itinerary_id)
                itinerary.title = item.get("title")
                itinerary.description = item.get("description")
                itinerary.meals = item.get("meals")
                itinerary.display_order = item.get("display_order", idx + 1)
                updated_ids.add(itinerary_id)
            else:
                new_itinerary = Tour_Itineraries(
                    tour_id=tour_id,
                    title=item.get("title"),
                    description=item.get("description"),
                    meals=item.get("meals"),
                    display_order=item.get("display_order", idx + 1)
                )
                db.session.add(new_itinerary)

        for itinerary in existing_itineraries:
            if itinerary.itinerary_id not in updated_ids:
                db.session.delete(itinerary)

        if errors:
            db.session.rollback()
            return jsonify({"message": "Lỗi xác nhận", "errors": errors}), 400
        
        db.session.commit()
        return jsonify({"message": "Cập nhật lịch trình chi tiết thành công"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi server: {str(e)}"}), 500