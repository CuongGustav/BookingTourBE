
from datetime import date
import uuid
from flask import current_app, jsonify, request
from src.marshmallow.library_ma_tour_schedules import tour_schedule_create_schema, tour_schedule_schema, tour_schedule_update_schema, tour_schedule_detail_schema
from src.model.model_tour import Tours
from src.model.model_tour_schedule import ScheduleStatusEnum, Tour_Schedules
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
        
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message": "Tour không tồn tại"}), 404
        
        created_schedules = []
        errors = []

        for idx, item in enumerate(schedules_data):
            try:
                errors_item = tour_schedule_create_schema.validate(item)
                if errors_item:
                    errors.append({"index": idx, "data": item, "errors": errors_item})
                    continue

                required_fields = ["departure_date", "return_date", "available_seats", 
                                 "price_adult", "price_child", "price_infant"]
                missing_fields = [field for field in required_fields if not item.get(field)]
                if missing_fields:
                    errors.append({
                        "index": idx, 
                        "data": item,
                        "errors": f"Thiếu các trường: {', '.join(missing_fields)}"
                    })
                    continue

                departure = item.get("departure_date")
                return_date = item.get("return_date")
                if return_date <= departure:
                    errors.append({
                        "index": idx,
                        "data": item, 
                        "errors": "Ngày về phải sau ngày đi"
                    })
                    continue

                existing = Tour_Schedules.query.filter_by(
                    tour_id=tour_id,
                    departure_date=departure
                ).first()
                if existing:
                    errors.append({
                        "index": idx,
                        "data": item,
                        "errors": "Lịch trình với ngày khởi hành này đã tồn tại"
                    })
                    continue

                new_schedule = Tour_Schedules(
                    tour_id=tour_id,
                    departure_date=departure,
                    return_date=return_date,
                    available_seats=item.get("available_seats"),
                    price_adult=item.get("price_adult"),
                    price_child=item.get("price_child"),
                    price_infant=item.get("price_infant")
                )
                db.session.add(new_schedule)
                created_schedules.append(new_schedule)
                
            except Exception as item_error:
                errors.append({
                    "index": idx,
                    "data": item,
                    "errors": str(item_error)
                })
                continue
        
        if errors:
            db.session.rollback()
            return jsonify({
                "message": "Có lỗi xảy ra khi tạo lịch trình",
                "total_sent": len(schedules_data),
                "total_valid": len(created_schedules),
                "total_errors": len(errors),
                "errors": errors
            }), 400
        
        db.session.commit()
        
        return jsonify({
            "message": "Tạo lịch trình khởi hành thành công",
            "total_created": len(created_schedules)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi tạo lịch trình: {str(e)}", exc_info=True)
        return jsonify({"message": f"Lỗi server: {str(e)}"}), 500
    
#get tour schedule
def get_tour_schedule_service(tour_id):
    if not tour_id:
        return jsonify({"message": "Thiếu tour_id"}), 400
    try:
        today = date.today()
        schedules = Tour_Schedules.query.filter(
            Tour_Schedules.tour_id == tour_id,
            Tour_Schedules.departure_date >= today
        ).order_by(Tour_Schedules.departure_date.asc()).all()
        
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
        if not tour_id:
            return jsonify({"message": "Thiếu tour_id"}), 400
        
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message": "Tour không tồn tại"}), 404
        
        if not schedules_data or len(schedules_data) == 0:
            return jsonify({"message": "Không có dữ liệu về Lịch trình khởi hành"}), 400
        
        existing_schedules = Tour_Schedules.query.filter_by(tour_id=tour_id).all()
        existing_ids = {schedule.schedule_id for schedule in existing_schedules}
        
        updated_ids = set()
        errors = []
        created_count = 0
        updated_count = 0

        for idx, item in enumerate(schedules_data):
            errors_item = tour_schedule_update_schema.validate(item)
            if errors_item:
                errors.append({"index": idx, "errors": errors_item})
                continue

            schedule_id = item.get("schedule_id")
            available_seats_new = item.get("available_seats")
            departure_date_new = item.get("departure_date")
            return_date_new = item.get("return_date")
            price_adult_new = item.get("price_adult")
            price_child_new = item.get("price_child") or 0
            price_infant_new = item.get("price_infant") or 0

            if schedule_id:
                try:
                    uuid.UUID(schedule_id)
                except ValueError:
                    errors.append({
                        "index": idx,
                        "message": "schedule_id không hợp lệ (phải là UUID)"
                    })
                    continue

            if available_seats_new <= 0:
                errors.append({"index": idx, "message": "Số chỗ phải > 0"})
                continue

            if price_adult_new <= 0:
                errors.append({"index": idx, "message": "Giá người lớn phải > 0"})
                continue

            if price_child_new >= price_adult_new:
                errors.append({"index": idx, "message": "Giá trẻ em phải < giá người lớn"})
                continue

            if price_infant_new >= price_child_new and price_child_new > 0:
                errors.append({"index": idx, "message": "Giá sơ sinh phải < giá trẻ em"})
                continue

            if return_date_new <= departure_date_new:
                errors.append({"index": idx, "message": "Ngày về phải sau ngày đi"})
                continue

            if not schedule_id:
                existing = Tour_Schedules.query.filter_by(
                    tour_id=tour_id,
                    departure_date=departure_date_new
                ).first()
                if existing:
                    errors.append({"index": idx, "message": "Ngày khởi hành này đã tồn tại cho tour"})
                    continue

                new_schedule = Tour_Schedules(
                    tour_id=tour_id,
                    departure_date=departure_date_new,
                    return_date=return_date_new,
                    available_seats=available_seats_new,
                    price_adult=price_adult_new,
                    price_child=price_child_new,
                    price_infant=price_infant_new
                )
                if new_schedule.available_seats <= 0:
                    new_schedule.status = ScheduleStatusEnum.FULL.value
                else:
                    new_schedule.status = ScheduleStatusEnum.AVAILABLE.value
                
                db.session.add(new_schedule)
                created_count += 1
                continue

            schedule = Tour_Schedules.query.get(schedule_id)
            if not schedule:
                existing = Tour_Schedules.query.filter_by(
                    tour_id=tour_id,
                    departure_date=departure_date_new
                ).first()
                if existing:
                    errors.append({"index": idx, "message": "Ngày khởi hành này đã tồn tại cho tour"})
                    continue

                new_schedule = Tour_Schedules(
                    tour_id=tour_id,
                    departure_date=departure_date_new,
                    return_date=return_date_new,
                    available_seats=available_seats_new,
                    price_adult=price_adult_new,
                    price_child=price_child_new,
                    price_infant=price_infant_new
                )
                new_schedule.schedule_id = schedule_id  
                if new_schedule.available_seats <= 0:
                    new_schedule.status = ScheduleStatusEnum.FULL.value
                else:
                    new_schedule.status = ScheduleStatusEnum.AVAILABLE.value
                
                db.session.add(new_schedule)
                created_count += 1
                updated_ids.add(schedule_id) 
                continue

            if schedule.tour_id != tour_id:
                errors.append({
                    "index": idx,
                    "schedule_id": schedule_id,
                    "message": "Lịch không thuộc tour này"
                })
                continue

            # check available_seats vs booked_seats
            if available_seats_new < schedule.booked_seats:
                errors.append({
                    "index": idx,
                    "schedule_id": schedule_id,
                    "message": f"Số ghế khả dụng ({available_seats_new}) không thể nhỏ hơn số ghế đã đặt ({schedule.booked_seats})"
                })
                continue

            # Check departure_date 
            existing = Tour_Schedules.query.filter(
                Tour_Schedules.tour_id == tour_id,
                Tour_Schedules.departure_date == departure_date_new,
                Tour_Schedules.schedule_id != schedule_id
            ).first()
            if existing:
                errors.append({"index": idx, "message": "Ngày khởi hành này đã tồn tại cho tour"})
                continue

            schedule.departure_date = departure_date_new
            schedule.return_date = return_date_new
            schedule.available_seats = available_seats_new
            schedule.price_adult = price_adult_new
            schedule.price_child = price_child_new
            schedule.price_infant = price_infant_new
            
            # Update status 
            if schedule.available_seats <= 0:
                schedule.status = ScheduleStatusEnum.FULL.value
            else:
                schedule.status = ScheduleStatusEnum.AVAILABLE.value
            
            updated_ids.add(schedule_id)
            updated_count += 1

        if errors:
            db.session.rollback()
            return jsonify({
                "message": "Cập nhật thất bại do có lỗi",
                "total_sent": len(schedules_data),
                "total_updated": updated_count,
                "total_created": created_count,
                "errors": errors
            }), 400
        
        db.session.commit()
        return jsonify({
            "message": "Cập nhật lịch trình khởi hành thành công",
            "total_updated": updated_count,
            "total_created": created_count
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi cập nhật lịch trình: {str(e)}", exc_info=True)
        return jsonify({"message": f"Lỗi server: {str(e)}"}), 500
    
#get tour schedule detail
def get_tour_schedule_detail_service(schedule_id):
    try:
        schedule = Tour_Schedules.query.get(schedule_id)
        if not schedule:
            return jsonify({"message": "Schedule không tồn tại"}), 404
        
        result = tour_schedule_detail_schema.dump(schedule)
        return jsonify({"data": result}), 200
    except Exception as e:
        return jsonify({"message": f"Lỗi server: {str(e)}"}), 500