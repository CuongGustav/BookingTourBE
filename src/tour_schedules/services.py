
from flask import jsonify, request
from src.marshmallow.library_ma_tour_schedules import tour_schedule_create_schema
from src.model.model_tour_schedule import Tour_Schedules
from src.extension import db

def create_tour_schedules_admin_service():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Dữ liệu gửi lên không hợp lệ"}), 400
        
        tour_id = data.get("tour_id")
        schedules_data = data.get("schedules")

        if not tour_id:
            return jsonify({"message": "Thiếu tour_id"}), 400
        if not schedules_data or len(schedules_data) == 0:
            return jsonify({"message": "Không có dữ liệu về Lịch trình khởi hành"}), 400
        
        created_schedules = []
        errors = []

        for idx, item in enumerate(schedules_data):
            # Validate item 
            errors_item = tour_schedule_create_schema.validate(item)
            if errors_item:
                errors.append({"index": idx, "errors": errors_item})
                continue

            new_schedule = Tour_Schedules(
                tour_id=tour_id,
                departure_date=item.get("departure_date"),
                return_date=item.get("return_date"),
                available_seats=item.get("available_seats"),
                price_adult=item.get("price_adult"),
                price_child=item.get("price_child"),
                price_infant=item.get("price_infant")
            )
            db.session.add(new_schedule)
            created_schedules.append(new_schedule)
        if errors:
            db.session.rollback()
            return jsonify({"message": "Lỗi xác nhận", "errors": errors}), 400
        
        db.session.commit()
        return jsonify({"message": "Tạo lịch trình khởi hành thành công"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi server: {str(e)}"}), 500