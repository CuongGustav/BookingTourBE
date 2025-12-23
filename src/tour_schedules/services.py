
from flask import current_app, jsonify, request
from src.marshmallow.library_ma_tour_schedules import tour_schedule_create_schema, tour_schedule_schema
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
    
#get tour schedule
def get_tour_schedule_service(tour_id):
    if not tour_id:
        return jsonify({"message": "Thiếu tour_id"}), 400
    try:
        schedules = Tour_Schedules.query.filter_by(tour_id=tour_id).all()
        
        if not schedules:
            return []
        
        result = tour_schedule_schema.dump(schedules)
        return result
    except Exception as e:
        print(f"[TourSchedulesService] Lỗi ở hàm get_tour_schedule_service {tour_id}: {str(e)}")
        db.session.rollback()
        return []
    
# update tour schedule
def update_tour_schedule_service(tour_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Dữ liệu gửi lên không hợp lệ"}), 400
        
        schedules_data = data.get("schedules")
        if not schedules_data or len(schedules_data) == 0:
            return jsonify({"message": "Không có dữ liệu về lịch khởi hành"}), 400

        # Lấy tất cả lịch hiện tại của tour
        existing_schedules = Tour_Schedules.query.filter_by(tour_id=tour_id).all()
        existing_schedule_map = {sch.schedule_id: sch for sch in existing_schedules}

        updated_schedule_ids = set()
        errors = []

        for idx, item in enumerate(schedules_data):
            validation_errors = tour_schedule_create_schema.validate(item)
            if validation_errors:
                errors.append({"index": idx, "errors": validation_errors})
                continue

            new_available_seats = item.get("available_seats")
            if new_available_seats is not None and new_available_seats < 0:
                errors.append({"index": idx, "error": "Số chỗ không được âm"})
                continue

            schedule_id = item.get("schedule_id")

            if schedule_id and schedule_id in existing_schedule_map:
                # Cập nhật lịch cũ
                schedule = existing_schedule_map[schedule_id]

                # Kiểm tra: available_seats mới không được nhỏ hơn booked_seats hiện tại
                if new_available_seats is not None:
                    if new_available_seats < schedule.booked_seats:
                        errors.append({
                            "index": idx,
                            "error": f"Số chỗ mới ({new_available_seats}) không được nhỏ hơn số chỗ đã đặt ({schedule.booked_seats})"
                        })
                        continue

                # Cập nhật các field
                schedule.departure_date = item["departure_date"]
                schedule.return_date = item["return_date"]
                schedule.available_seats = new_available_seats
                schedule.price_adult = item["price_adult"]
                schedule.price_child = item.get("price_child")
                schedule.price_infant = item.get("price_infant")

                # Tự động cập nhật status nếu cần (tùy yêu cầu)
                # Ví dụ: nếu available_seats == booked_seats → full
                if schedule.available_seats <= schedule.booked_seats:
                    schedule.status = "full"
                elif schedule.booked_seats == 0:
                    schedule.status = "available"
                # Có thể thêm logic cancelled nếu cần

                updated_schedule_ids.add(schedule_id)

            else:
                # Tạo mới lịch khởi hành
                new_schedule = Tour_Schedules(
                    tour_id=tour_id,
                    departure_date=item["departure_date"],
                    return_date=item["return_date"],
                    available_seats=new_available_seats,
                    price_adult=item["price_adult"],
                    price_child=item.get("price_child"),
                    price_infant=item.get("price_infant"),
                    # booked_seats mặc định 0, status mặc định available
                )
                db.session.add(new_schedule)

        # Xóa các lịch cũ không còn trong danh sách
        for schedule in existing_schedules:
            if schedule.schedule_id not in updated_schedule_ids:
                # Bonus: Kiểm tra trước khi xóa — nếu đã có booking thì không cho xóa
                if schedule.booked_seats > 0:
                    errors.append({
                        "schedule_id": schedule.schedule_id,
                        "error": f"Không thể xóa lịch khởi hành vì đã có {schedule.booked_seats} booking"
                    })
                    continue
                db.session.delete(schedule)

        if errors:
            db.session.rollback()
            return jsonify({
                "message": "Có lỗi khi cập nhật lịch khởi hành",
                "errors": errors
            }), 400

        db.session.commit()
        return jsonify({"message": "Cập nhật lịch khởi hành thành công"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi cập nhật lịch khởi hành tour {tour_id}: {str(e)}", exc_info=True)
        return jsonify({
            "message": "Cập nhật lịch khởi hành thất bại",
            "error": str(e)
        }), 500