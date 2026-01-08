from datetime import datetime
import uuid
from flask import jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from sqlalchemy.orm import joinedload
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_tour import Tours
from src.model.model_coupon import Coupons
from src.booking_passengers.services import create_booking_passenger_service
from src.model.model_tour_schedule import Tour_Schedules
from src.marshmallow.library_ma_booking import read_booking_user_schema, read_one_booking_user_schema

def generate_booking_code():
    current_date = datetime.now().strftime("%Y%m%d")
    prefix = f"BK-{current_date}"

    last_booking = Bookings.query.filter(
        Bookings.booking_code.like(f"{prefix}%")
    ).order_by(Bookings.created_at.desc()).first()

    if not last_booking or not last_booking.booking_code:
        new_code = f"{prefix}-A0001"
    else:
        code_part = last_booking.booking_code.split('-')[-1]
        if len(code_part) != 5:
            new_code = f"{prefix}-A0001"
        else:
            group_letter = code_part[0]
            number_part = code_part[1:]
            try:
                num = int(number_part) + 1
                if num <= 9999:
                    new_code = f"{prefix}-{group_letter}{str(num).zfill(4)}"
                else:
                    next_letter = chr(ord(group_letter) + 1) if group_letter != 'Z' else 'A'
                    new_code = f"{prefix}-{next_letter}0001"
            except ValueError:
                new_code = f"{prefix}-A0001"

    while Bookings.query.filter_by(booking_code=new_code).first():
        random_part = uuid.uuid4().hex[:5].upper()
        new_code = f"{prefix}-{random_part}"

    return new_code

def create_booking_service():
    data = request.get_json()
    try:
        account_id = get_jwt_identity()
        if not account_id:
            return jsonify({"message": "Không tìm thấy account_id từ token"}), 401

        schedule_id = data.get("schedule_id")
        schedule = Tour_Schedules.query.get(schedule_id)
        
        if not schedule:
            return jsonify({"message": "Lịch trình không tồn tại"}), 404

        tour = Tours.query.get(data["tour_id"])
        if not tour:
            return jsonify({"message": "Tour không tồn tại"}), 404

        num_adults = data["num_adults"]
        num_children = data.get("num_children", 0)
        num_infants = data.get("num_infants", 0)

        passengers = data.get("passengers", [])
        num_single_rooms = sum(1 for p in passengers if p.get("single_room", False))

        #passengers
        actual_adults = sum(1 for p in passengers if p["passenger_type"].lower() == "adult")
        actual_children = sum(1 for p in passengers if p["passenger_type"].lower() == "child")
        actual_infants = sum(1 for p in passengers if p["passenger_type"].lower() == "infant")
        if (actual_adults != num_adults or
            actual_children != num_children or
            actual_infants != num_infants):
            return jsonify({"message": "Số lượng hành khách không khớp"}), 400

        #total_price
        total_price = (
            num_adults * schedule.price_adult + 
            num_children * schedule.price_child + 
            num_infants * schedule.price_infant + 
            num_single_rooms * tour.single_room_surcharge 
        )

        #coupon
        discount_amount = 0
        coupon_id = data.get("coupon_id")
        if coupon_id:
            coupon = Coupons.query.get(coupon_id)
            if not coupon:
                return jsonify({"message": "Coupon không tồn tại"}), 404
            now = datetime.now()
            if coupon.valid_from > now or coupon.valid_to < now:
                return jsonify({"message": "Coupon đã hết hạn"}), 400
            if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
                return jsonify({"message": "Coupon đã hết lượt sử dụng"}), 400

            if coupon.discount_type == "percentage":
                discount_amount = total_price * (coupon.discount_value / 100)
            elif coupon.discount_type == "fixed":
                discount_amount = coupon.discount_value
            if coupon.max_discount_amount and discount_amount > coupon.max_discoun_amount:
                discount_amount = coupon.max_discount

        final_price = total_price - discount_amount

        booking_code = generate_booking_code()

        booking = Bookings(
            booking_code=booking_code,
            account_id=account_id,
            tour_id=data["tour_id"],
            schedule_id=data["schedule_id"],
            coupon_id=coupon_id,
            num_adults=num_adults,
            num_children=num_children,
            num_infants=num_infants,
            total_price=total_price,
            discount_amount=discount_amount,
            final_price=final_price,
            contact_name=data["contact_name"],
            contact_email=data["contact_email"],
            contact_phone=data["contact_phone"],
            contact_address=data["contact_address"],
            special_request=data.get("special_request"),
            status=BookingStatusEnum.PENDING.value,
        )

        db.session.add(booking)
        db.session.flush()

        booking_id = booking.booking_id

        # passengers
        for passenger_data in passengers:
            create_booking_passenger_service(
                booking_id=booking_id,
                passenger_type=passenger_data["passenger_type"].upper(),
                full_name=passenger_data["full_name"],
                date_of_birth=passenger_data.get("date_of_birth"),
                gender=passenger_data.get("gender"),
                id_number=passenger_data.get("id_number"),
                single_room=passenger_data.get("single_room", False)
            )

        db.session.commit()

        return jsonify({
            "message": "Đặt chỗ thành công",
            "booking_id": booking.booking_id,
            "booking_code": booking.booking_code
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi tạo booking: {str(e)}", exc_info=True)
        return jsonify({
            "message": "Đặt chỗ thất bại",
            "error": str(e)
        }), 500
    
#get all booking by account id
def get_bookings_user_service():
    try:
        account_id = get_jwt_identity()
        if not account_id:
            return jsonify({"message": "Không tìm thấy account_id từ token"}), 401
        
        status = request.args.get("status")
        query = Bookings.query.options(joinedload(Bookings.tour)).filter_by(account_id=account_id)

        if status:
            status_upper = status.upper()
            if status_upper in BookingStatusEnum.__members__:
                query = query.filter_by(status=status_upper)
            else:
                return jsonify({"message": "Trạng thái không hợp lệ"}), 400

        bookings = query.order_by(Bookings.created_at.desc()).all()
        bookings_data = read_booking_user_schema.dump(bookings)

        return jsonify({"bookings": bookings_data}), 200
    except Exception as e:
        current_app.logger.error(f"Lỗi lấy bookings: {str(e)}", exc_info=True)
        return jsonify({"message": "Lấy bookings thất bại", "error": str(e)}), 500
    
#get all booking by booking id
def get_booking_by_id_service(booking_id):
    try:
        account_id = get_jwt_identity()
        if not account_id:
            return jsonify({"message": "Không tìm thấy account_id"}), 401

        booking = Bookings.query.options(
            joinedload(Bookings.tour),
            joinedload(Bookings.passengers)
        ).filter_by(booking_id=booking_id, account_id=account_id).first()

        if not booking:
            return jsonify({"message": "Booking không tồn tại hoặc không thuộc về bạn"}), 404

        booking_data = read_one_booking_user_schema.dump(booking)

        return jsonify({"booking": booking_data}), 200
    except Exception as e:
        current_app.logger.error(f"Lỗi lấy booking: {str(e)}", exc_info=True)
        return jsonify({"message": "Lấy booking thất bại", "error": str(e)}), 500
    
def cancel_booking_service(booking_id):
    try:
        account_id = get_jwt_identity()
        data = request.get_json() or {} 
        reason = data.get("cancellation_reason", "Người dùng tự yêu cầu hủy")

        booking = Bookings.query.filter_by(
            booking_id=booking_id, 
            account_id=account_id
        ).first()

        if not booking:
            return jsonify({"message": "Booking không tồn tại hoặc không thuộc về bạn"}), 404

        if booking.status == BookingStatusEnum.CANCELLED.value:
            return jsonify({"message": "Đơn hàng này đã được hủy trước đó"}), 400
        
        if booking.status == BookingStatusEnum.COMPLETED.value:
            return jsonify({"message": "Không thể hủy đơn hàng đã hoàn thành"}), 400

        booking.status = BookingStatusEnum.CANCELLED.value
        booking.cancelled_at = datetime.now()
        booking.cancellation_reason = reason 
        
        db.session.commit()

        return jsonify({
            "message": "Hủy đơn đặt tour thành công",
            "booking_id": booking_id
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi hủy booking: {str(e)}", exc_info=True)
        return jsonify({"message": "Hủy đơn đặt tour thất bại", "error": str(e)}), 500