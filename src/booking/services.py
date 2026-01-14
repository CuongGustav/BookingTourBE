from datetime import datetime
import uuid
from flask import jsonify, request, current_app
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from sqlalchemy.orm import joinedload
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_payment import PaymentStatusEnum, Payments
from src.model.model_review import Reviews
from src.model.model_tour import Tours
from src.model.model_coupon import Coupons, DiscountTypeEnum
from src.booking_passengers.services import create_booking_passenger_service, update_booking_passengers_service
from src.model.model_tour_schedule import Tour_Schedules
from src.marshmallow.library_ma_booking import read_booking_user_schema, read_one_booking_user_schema
from src.payment.services import calculate_refund_amount
from src.payment_images.services import create_payment_image

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
                discount_amount = coupon.max_discount_amount

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
        query = Bookings.query.options(
            joinedload(Bookings.tour),
            joinedload(Bookings.reviews)
        ).filter_by(account_id=account_id)

        if status:
            status_upper = status.upper()
            if status_upper in BookingStatusEnum.__members__:
                query = query.filter_by(status=status_upper)
            else:
                return jsonify({"message": "Trạng thái không hợp lệ"}), 400

        bookings = query.order_by(Bookings.created_at.desc()).all()
        
        bookings_data = read_booking_user_schema.dump(bookings)
        
        for i, booking in enumerate(bookings):
            has_reviewed = len(booking.reviews) > 0 if booking.reviews else False
            bookings_data[i]['is_review'] = has_reviewed

        return jsonify({"bookings": bookings_data}), 200
    except Exception as e:
        current_app.logger.error(f"Lỗi lấy bookings: {str(e)}", exc_info=True)
        return jsonify({"message": "Lấy bookings thất bại", "error": str(e)}), 500
    
#get booking by booking id
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

        has_reviewed = Reviews.query.filter_by(booking_id=booking_id, account_id=account_id).first() is not None
        booking_data['is_review'] = has_reviewed

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
    
#update booking
def update_booking_service():
    data = request.get_json()
    try:
        account_id = get_jwt_identity()
        if not account_id:
            return jsonify({"message": "Không tìm thấy account_id từ token"}), 401

        booking_id = data.get("booking_id")
        if not booking_id:
            return jsonify({"message": "Thiếu booking_id trong request"}), 400

        booking = Bookings.query.filter_by(
            booking_id=booking_id, 
            account_id=account_id
        ).first()

        if not booking:
            return jsonify({"message": "Booking không tồn tại hoặc không thuộc về bạn"}), 404

        if str(booking.status.value).lower() != str(BookingStatusEnum.PENDING.value).lower():
            return jsonify({"message": "Chỉ có thể cập nhật booking ở trạng thái PENDING"}), 400

        schedule_id = data.get("schedule_id", booking.schedule_id)
        schedule = Tour_Schedules.query.get(schedule_id)
        if not schedule:
            return jsonify({"message": "Lịch trình không tồn tại"}), 404

        tour_id = data.get("tour_id", booking.tour_id)
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message": "Tour không tồn tại"}), 404

        num_adults = data.get("num_adults", booking.num_adults)
        num_children = data.get("num_children", booking.num_children)
        num_infants = data.get("num_infants", booking.num_infants)

        # Passengers
        passengers_data = data.get("passengers", [])
        if passengers_data:
            actual_adults = sum(1 for p in passengers_data if p["passenger_type"].lower() == "adult")
            actual_children = sum(1 for p in passengers_data if p["passenger_type"].lower() == "child")
            actual_infants = sum(1 for p in passengers_data if p["passenger_type"].lower() == "infant")
            
            if (actual_adults != num_adults or
                actual_children != num_children or
                actual_infants != num_infants):
                return jsonify({"message": "Số lượng hành khách không khớp với danh sách cung cấp"}), 400

            valid_genders = {"MALE", "FEMALE", "OTHER"}
            for p in passengers_data:
                if not p.get("full_name"):
                    return jsonify({"message": "Họ tên hành khách bắt buộc"}), 400
                if not p.get("date_of_birth"):
                    return jsonify({"message": "Ngày sinh hành khách bắt buộc"}), 400
                try:
                    datetime.fromisoformat(p["date_of_birth"].replace('Z', '+00:00'))
                except ValueError:
                    return jsonify({"message": "Định dạng ngày sinh không hợp lệ"}), 400
                if p.get("gender") not in valid_genders:
                    return jsonify({"message": "Giới tính không hợp lệ"}), 400

            update_result = update_booking_passengers_service(booking_id, passengers_data, num_adults, num_children, num_infants)
            
            if not isinstance(update_result, int):
                return update_result
            
            num_single_rooms = update_result 
        else:
            num_single_rooms = sum(1 for p in booking.passengers if p.single_room)

        total_price = (
            num_adults * schedule.price_adult + 
            num_children * schedule.price_child + 
            num_infants * schedule.price_infant + 
            num_single_rooms * tour.single_room_surcharge 
        )

        discount_amount = 0 
        coupon_id = data.get("coupon_id", booking.coupon_id)
        if coupon_id:
            coupon = Coupons.query.get(coupon_id)
            if coupon:
                now = datetime.now()
                if coupon.valid_from > now or coupon.valid_to < now:
                    return jsonify({"message": "Coupon đã hết hạn"}), 400
                if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
                    return jsonify({"message": "Coupon đã hết lượt sử dụng"}), 400
                if total_price < coupon.min_order_amount:
                    return jsonify({"message": f"Đơn hàng tối thiểu {coupon.min_order_amount}đ để dùng coupon này"}), 400


                if coupon.discount_type == DiscountTypeEnum.PERCENTAGE:
                    discount_amount = total_price * (coupon.discount_value / 100)
                elif coupon.discount_type == DiscountTypeEnum.FIXED:
                    discount_amount = coupon.discount_value
                
                if coupon.max_discount_amount and discount_amount > coupon.max_discount_amount:
                    discount_amount = coupon.max_discount_amount

        final_price = max(0, total_price - discount_amount)

        booking.tour_id = tour_id
        booking.schedule_id = schedule_id
        booking.coupon_id = coupon_id
        booking.num_adults = num_adults
        booking.num_children = num_children
        booking.num_infants = num_infants
        booking.total_price = total_price
        booking.discount_amount = discount_amount
        booking.final_price = final_price
        booking.contact_name = data.get("contact_name", booking.contact_name)
        booking.contact_email = data.get("contact_email", booking.contact_email)
        booking.contact_phone = data.get("contact_phone", booking.contact_phone)
        booking.contact_address = data.get("contact_address", booking.contact_address)
        booking.special_request = data.get("special_request", booking.special_request)
        booking.updated_at = datetime.now() 

        db.session.commit()

        return jsonify({
            "message": "Cập nhật booking thành công",
            "booking_id": booking.booking_id,
            "booking_code": booking.booking_code
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi cập nhật booking: {str(e)}", exc_info=True)
        return jsonify({
            "message": "Cập nhật booking thất bại",
            "error": str(e)
        }), 500
    
#get all booking admin
def get_all_booking_admin_service():
    try:
        bookings = Bookings.query.order_by(Bookings.created_at.desc()).all()
        if not bookings:
            return jsonify({"message":"Không có booking nào trong hệ thống", "data":[]}),200
        return read_booking_user_schema.dump(bookings), 200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách booking: {str(e)}"}), 500  
    
#read booking detail admin
def read_booking_detail_admin_service(booking_id):
    try:
        if not booking_id:
            return jsonify({"message":"Không có booking_id"}),400
        booking = Bookings.query.filter_by(booking_id= booking_id).first()
        if not booking:
            return jsonify({"message":"Không có booking nào trong hệ thống", "data":[]}),200
        return read_one_booking_user_schema.dump(booking),200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách booking: {str(e)}"}), 500  
    
#cancel booking pending admin
def cancel_booking_pending_admin_service(booking_id):
    try:
        data = request.get_json() or {} 
        reason = data.get("cancellation_reason", "Người dùng tự yêu cầu hủy")
        
        if not booking_id:
            return jsonify({"message":"Không có booking_id"}),400
        
        booking = Bookings.query.filter_by(booking_id=booking_id).first()
        if not booking:
            return jsonify({"message": "Booking không tồn tại"}), 404
        
        if booking.status == BookingStatusEnum.CANCELLED:
            return jsonify({"message": "Đơn hàng này đã được hủy trước đó"}), 400
        
        if booking.status == BookingStatusEnum.COMPLETED:
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
        
#cancel booking paid admin
def cancel_booking_paid_admin_service(booking_id):
    try:
        data = request.get_json() or {} 
        reason = data.get("cancellation_reason", "Admin hủy đơn hàng đã thanh toán")
        
        if not booking_id:
            return jsonify({"message":"Không có booking_id"}), 400
        
        booking = Bookings.query.filter_by(booking_id=booking_id).first()
        if not booking:
            return jsonify({"message": "Booking không tồn tại"}), 404
        
        if booking.status == BookingStatusEnum.CANCELLED:
            return jsonify({"message": "Đơn hàng này đã được hủy trước đó"}), 400
        
        if booking.status == BookingStatusEnum.COMPLETED:
            return jsonify({"message": "Không thể hủy đơn hàng đã hoàn thành"}), 400
        
        if booking.status != BookingStatusEnum.PAID:
            return jsonify({"message": "Chỉ có thể hủy booking ở trạng thái PAID"}), 400
        
        # Tìm payment tương ứng với booking
        from src.model.model_payment import Payments, PaymentStatusEnum
        payment = Payments.query.filter_by(booking_id=booking_id).first()
        
        if not payment:
            return jsonify({"message": "Không tìm thấy thanh toán cho booking này"}), 404
        
        booking.status = BookingStatusEnum.CANCELLED
        booking.cancelled_at = datetime.now()
        booking.cancellation_reason = reason
        
        payment.status = PaymentStatusEnum.FAILED
    
        db.session.commit()

        return jsonify({
            "message": "Hủy đơn đặt tour đã thanh toán thành công",
            "booking_id": booking_id,
            "booking_code": booking.booking_code
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi hủy booking paid: {str(e)}", exc_info=True)
        return jsonify({"message": "Hủy đơn đặt tour thất bại", "error": str(e)}), 500
    
#confirm booking paid admin
def confirm_booking_paid_admin_service(booking_id):
    try:
        if not booking_id:
            return jsonify({"message":"Không có booking_id"}), 400
        
        booking = Bookings.query.filter_by(booking_id=booking_id).first()
        if not booking:
            return jsonify({"message": "Booking không tồn tại"}), 404
        
        if booking.status == BookingStatusEnum.CONFIRMED:
            return jsonify({"message": "Đơn hàng này đã được xác nhận trước đó"}), 400
        
        if booking.status == BookingStatusEnum.CANCELLED:
            return jsonify({"message": "Không thể xác nhận đơn hàng đã hủy"}), 400
        
        if booking.status == BookingStatusEnum.COMPLETED:
            return jsonify({"message": "Đơn hàng đã hoàn thành"}), 400
        
        if booking.status != BookingStatusEnum.PAID:
            return jsonify({"message": "Chỉ có thể xác nhận booking ở trạng thái PAID"}), 400
        
        from src.model.model_payment import Payments, PaymentStatusEnum
        payment = Payments.query.filter_by(booking_id=booking_id).first()
        
        if not payment:
            return jsonify({"message": "Không tìm thấy thanh toán cho booking này"}), 404
        
        schedule = Tour_Schedules.query.get(booking.schedule_id)
        if not schedule:
            return jsonify({"message": "Không tìm thấy lịch trình"}), 404
        
        total_passengers = booking.num_adults + booking.num_children + booking.num_infants
        
        if schedule.booked_seats + total_passengers > schedule.available_seats:
            return jsonify({"message": "Không đủ chỗ trống trong lịch trình"}), 400
        
        booking.status = BookingStatusEnum.CONFIRMED
        
        payment.status = PaymentStatusEnum.COMPLETED
        
        schedule.booked_seats += total_passengers
        
        from src.model.model_tour_schedule import ScheduleStatusEnum
        if schedule.booked_seats >= schedule.available_seats:
            schedule.status = ScheduleStatusEnum.FULL
        
        db.session.commit()

        return jsonify({
            "message": "Xác nhận booking thành công",
            "booking_id": booking_id,
            "booking_code": booking.booking_code
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi xác nhận booking: {str(e)}", exc_info=True)
        return jsonify({"message": "Xác nhận booking thất bại", "error": str(e)}), 500  
    
#cancel booking confirm user
def cancel_booking_confirmed_user_service(booking_id):
    try:
        account_id = get_jwt_identity()
        if not account_id:
            return jsonify({"message": "Không tìm thấy account_id từ token"}), 401

        data = request.get_json() or {}
        reason = data.get("cancellation_reason", "").strip()

        if not reason:
            return jsonify({"message": "Vui lòng nhập lý do hủy (bắt buộc phải có thông tin tài khoản để hoàn tiền)"}), 400

        if not booking_id:
            return jsonify({"message": "Không có booking_id"}), 400

        booking = Bookings.query.filter_by(
            booking_id=booking_id,
            account_id=account_id
        ).first()

        if not booking:
            return jsonify({"message": "Booking không tồn tại hoặc không thuộc về bạn"}), 404

        if booking.status == BookingStatusEnum.CANCELLED:
            return jsonify({"message": "Đơn hàng này đã được hủy trước đó"}), 400
        if booking.status == BookingStatusEnum.CANCEL_PENDING:
            return jsonify({"message": "Đơn hàng đang chờ xử lý hủy"}), 400
        if booking.status == BookingStatusEnum.COMPLETED:
            return jsonify({"message": "Không thể hủy đơn hàng đã hoàn thành"}), 400
        if booking.status == BookingStatusEnum.PAID:
            return jsonify({"message": "Đơn hàng chưa được xác nhận, vui lòng sử dụng chức năng hủy đơn hàng chưa xác nhận"}), 400

        if booking.status != BookingStatusEnum.CONFIRMED:
            return jsonify({"message": "Chỉ có thể hủy booking đã được xác nhận (CONFIRMED)"}), 400

        from src.model.model_payment import Payments
        payment = Payments.query.filter_by(booking_id=booking_id).first()

        if not payment:
            return jsonify({"message": "Không tìm thấy thanh toán cho booking này"}), 404

        booking.status = BookingStatusEnum.CANCEL_PENDING.value
        booking.cancellation_reason = reason
        booking.cancelled_at = datetime.now()

        db.session.commit()

        return jsonify({
            "message": "Yêu cầu hủy đơn đặt tour đã được gửi. Admin sẽ xử lý hoàn tiền trong thời gian sớm nhất",
            "booking_id": booking_id,
            "booking_code": booking.booking_code,
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi hủy booking confirmed user: {str(e)}", exc_info=True)
        return jsonify({"message": "Hủy đơn đặt tour thất bại", "error": str(e)}), 500
    
#cancel booking and refunded payment confirmed admin
def cancel_booking_confirm_and_refund_payment_admin_service(booking_id):
    try:
        data = request.form
        files = request.files.getlist("images")

        cancellation_reason = data.get("cancellation_reason")
        payment_method = data.get("payment_method")
        amount = data.get("amount")

        if not all([cancellation_reason, payment_method, amount]):
            return jsonify({"message": "Thiếu dữ liệu"}), 400
        try:
            refund_amount = float(amount)
            if refund_amount <= 0:
                return jsonify({"message": "Số tiền hoàn trả phải lớn hơn 0"}), 400
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        booking.status = BookingStatusEnum.CANCELLED.value
        booking.cancellation_reason = cancellation_reason

        refund_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=float(amount),
            status=PaymentStatusEnum.REFUNDED.value,
        )
        db.session.add(refund_payment)
        db.session.flush()

        if files and files[0].filename:
            create_payment_image(refund_payment.payment_id, files)

        schedule = Tour_Schedules.query.get(booking.schedule_id)
        if schedule:
            total_passengers = booking.num_adults + booking.num_children + booking.num_infants
            schedule.booked_seats = max(0, schedule.booked_seats - total_passengers)
            
            from src.model.model_tour_schedule import ScheduleStatusEnum
            if schedule.status == ScheduleStatusEnum.FULL.value and schedule.booked_seats < schedule.available_seats:
                schedule.status = ScheduleStatusEnum.AVAILABLE.value

        db.session.commit()

        return jsonify({
            "message": "Hủy booking & hoàn tiền thành công",
            "payment_id": refund_payment.payment_id
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(str(e))
        return jsonify({
            "message": "Lỗi khi hủy & hoàn tiền",
            "error": str(e)
        }), 500
    
#confirm booking cancel pending and refund payment admin
def confirm_booking_cancel_pending_and_refund_payment_admin_service(booking_id):
    try:
        data = request.form
        files = request.files.getlist("images")

        cancellation_reason = data.get("cancellation_reason")
        payment_method = data.get("payment_method")
        amount = data.get("amount")

        if not all([cancellation_reason, payment_method, amount]):
            return jsonify({"message": "Thiếu dữ liệu"}), 400
        
        try:
            refund_amount = float(amount)
            if refund_amount <= 0:
                return jsonify({"message": "Số tiền hoàn trả phải lớn hơn 0"}), 400
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404
        
        original_payment = Payments.query.filter_by(
            booking_id=booking_id,
            status=PaymentStatusEnum.COMPLETED.value
        ).first()
        if not original_payment:
            return jsonify({"message": "Không tìm thấy thanh toán gốc"}), 404
        refund_info = calculate_refund_amount(booking, original_payment.amount)
        
        if not refund_info:
            return jsonify({"message": "Không thể tính toán số tiền hoàn trả"}), 400

        calculated_refund = refund_info['refund_amount']
        if abs(refund_amount - calculated_refund) > 1000:
            return jsonify({"message": f"Số tiền hoàn trả không khớp."}), 400

        booking.status = BookingStatusEnum.CANCELLED.value
        booking.cancellation_reason = cancellation_reason

        refund_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=float(amount),
            status=PaymentStatusEnum.REFUNDED.value,
        )
        db.session.add(refund_payment)
        db.session.flush()

        if files and files[0].filename:
            create_payment_image(refund_payment.payment_id, files)

        schedule = Tour_Schedules.query.get(booking.schedule_id)
        if schedule:
            total_passengers = booking.num_adults + booking.num_children + booking.num_infants
            schedule.booked_seats = max(0, schedule.booked_seats - total_passengers)
            
            # Update schedule status if it was FULL
            from src.model.model_tour_schedule import ScheduleStatusEnum
            if schedule.status == ScheduleStatusEnum.FULL.value and schedule.booked_seats < schedule.available_seats:
                schedule.status = ScheduleStatusEnum.AVAILABLE.value

        db.session.commit()

        return jsonify({
            "message": "Hủy booking & hoàn tiền thành công",
            "payment_id": refund_payment.payment_id
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(str(e))
        return jsonify({
            "message": "Lỗi khi hủy & hoàn tiền",
            "error": str(e)
        }), 500

#cancel booking cancel pending admin
def cancel_booking_cancel_pending_admin_service(booking_id):
    try:
        if not booking_id:
            return jsonify({"message": "Không có booking_id"}), 400
        
        booking = Bookings.query.filter_by(booking_id=booking_id).first()
        if not booking:
            return jsonify({"message": "Booking không tồn tại"}), 404
        
        if booking.status != BookingStatusEnum.CANCEL_PENDING:
            return jsonify({"message": "Chỉ có thể từ chối yêu cầu hủy với booking ở trạng thái CANCEL_PENDING"}), 400
        
        booking.status = BookingStatusEnum.CONFIRMED.value
        booking.cancellation_reason = None
        booking.cancelled_at = None
        
        db.session.commit()

        return jsonify({
            "message": "Đã từ chối yêu cầu hủy booking.",
            "booking_id": booking_id,
            "booking_code": booking.booking_code
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi từ chối hủy booking: {str(e)}", exc_info=True)
        return jsonify({"message": "Từ chối hủy booking thất bại", "error": str(e)}), 500