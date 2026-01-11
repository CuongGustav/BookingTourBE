from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from src.model.model_payment import Payments, PaymentMethodEnum, PaymentStatusEnum
from src.model.model_booking import Bookings, BookingStatusEnum
from datetime import datetime
from src.payment_images.services import create_payment_image


def create_payment_service():
    try:
        account_id = get_jwt_identity()
        data = request.form
        booking_id = data.get("booking_id")
        payment_method = data.get("payment_method")
        amount = data.get("amount")

        if not all([booking_id, payment_method, amount]):
            return jsonify({"message": "Thiếu thông tin: booking_id, payment_method, amount"}), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"message": "Thiếu giá"}), 400

        if payment_method not in [e.value for e in PaymentMethodEnum]:
            return jsonify({"message": "Phương thức thanh toán không hợp lệ"}), 400

        # Check booking exists
        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        # Check authorization
        if booking.account_id != account_id:
            return jsonify({"message": "Sai tài khoản"}), 403

        # Check booking status
        if booking.status != BookingStatusEnum.PENDING:
            return jsonify({"message": "Booking không phải ở trạng thái đang xử lý"}), 400

        new_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=amount,
            status=PaymentStatusEnum.PENDING.value,
            payment_date=datetime.utcnow()
        )
        db.session.add(new_payment)
        db.session.flush()  

        files = request.files.getlist("images")
        uploaded_images = []
        
        if files and len(files) > 0 and files[0].filename != '':
            try:
                uploaded_images = create_payment_image(new_payment.payment_id, files)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "upload ảnh thất bại",
                    "error": str(e)
                }), 400

        # Update booking status to paid
        booking.status = BookingStatusEnum.PAID.value
        
        # Commit all changes
        db.session.commit()

        response_data = {
            "message": "Thanh toán thành công",
            "payment_id": new_payment.payment_id
        }
        
        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo thanh toán: {str(e)}")
        return jsonify({"message": "Lỗi khi tạo thanh toán", "error": str(e)}), 500