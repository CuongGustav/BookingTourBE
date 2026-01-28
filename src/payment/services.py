from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from src.model.model_payment import Payments, PaymentMethodEnum, PaymentStatusEnum
from src.model.model_booking import Bookings, BookingStatusEnum
from datetime import datetime
from src.model.model_tour_schedule import ScheduleStatusEnum, Tour_Schedules
from src.payment_images.services import create_payment_image
import qrcode
import io
import base64
import crc16
from src.marshmallow.library_ma_payment import payments_schema, readPaymentDetailAdmin_schema

#create payment 
def create_payment_service():
    try:
        data = request.form

        booking_id = data.get("booking_id")
        payment_method = data.get("payment_method")
        amount = data.get("amount")

        if not all([booking_id, payment_method, amount]):
            return jsonify({
                "message": "Thiếu thông tin: booking_id, payment_method, amount"
            }), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        if payment_method not in [e.value for e in PaymentMethodEnum]:
            return jsonify({"message": "Phương thức thanh toán không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        final_price = float(booking.final_price)
        
        deposit_amount = final_price * 0.4
        
        diff_deposit = abs(amount - deposit_amount)
        diff_full = abs(amount - final_price)
        
        if diff_full <= 1000:
            is_full_payment = 1
            remaining_amount = 0.0
            new_status = BookingStatusEnum.PAID.value
        elif diff_deposit <= 1000:
            is_full_payment = 0
            remaining_amount = final_price - amount
            new_status = BookingStatusEnum.DEPOSIT.value 
        else:
            return jsonify({
                "message": f"Số tiền không hợp lệ. Chọn: {int(deposit_amount):,}đ (đặt cọc 40%) hoặc {int(final_price):,}đ (thanh toán 100%)"
            }), 400

        new_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=amount,
            status=PaymentStatusEnum.PENDING.value,
        )

        db.session.add(new_payment)
        db.session.flush()

        files = request.files.getlist("images")
        uploaded_images = []

        if files and len(files) > 0 and files[0].filename != '':
            try:
                uploaded_images = create_payment_image(
                    new_payment.payment_id,
                    files
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "Upload ảnh thất bại",
                    "error": str(e)
                }), 400

        # Cập nhật booking
        if booking.paid_money is None:
            booking.paid_money = 0

        booking.paid_money = float(booking.paid_money) + amount
        booking.is_full_payment = is_full_payment
        booking.remaining_amount = remaining_amount 
        booking.status = new_status

        db.session.commit()

        response_data = {
            "message": "Tạo thanh toán thành công",
            "payment_id": new_payment.payment_id,
            "booking_code": booking.booking_code,
            "is_full_payment": booking.is_full_payment,
            "paid_money": booking.paid_money,
            "remaining_amount": booking.remaining_amount  
        }

        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo thanh toán (admin): {str(e)}")
        return jsonify({
            "message": "Lỗi khi tạo thanh toán",
            "error": str(e)
        }), 500

# Tính mã CRC để xác thực tính toàn vẹn của dữ liệu QR, kiểm tra xem QR có hợp lệ không
def calculate_crc(data):
    crc = 0xFFFF #Giá trị ban đầu theo chuẩn CCITT-FALSE
    for byte in data.encode('utf-8'):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return format(crc, '04X')

#Tạo ra chuỗi dữ liệu QR thanh toán theo chuẩn VietQR
def build_vietqr_string(bank_bin, account_no, amount, description):
 
    def build_field(field_id, value):
        """Helper function để build từng field theo format: ID + Length + Value"""
        length = len(str(value))
        return f"{field_id:02d}{length:02d}{value}"
    
    qr_string = build_field(0, "01") # định dạng bắt buộc là 01
    
    # Point of Initiation Method (12 = QR tĩnh có thể dùng nhiều lần)
    qr_string += build_field(1, "12")
    
    # Merchant Account Information - VietQR
    # Field 38 cho VietQR
    vietqr_data = ""
    vietqr_data += build_field(0, "A000000727")  # GUID cho VietQR
    
    # khởi tạo thông tin người nhận tiền
    beneficiary = ""
    beneficiary += build_field(0, bank_bin)  # Bank BIN
    beneficiary += build_field(1, account_no)  # Account number
    
    vietqr_data += build_field(1, beneficiary)
    
    # Service code (field 2) - QRIBFTTA cho chuyển khoản
    vietqr_data += build_field(2, "QRIBFTTA")
    
    qr_string += build_field(38, vietqr_data)
    
    # Transaction Currency (704 = VND)
    qr_string += build_field(53, "704")
    
    # Transaction Amount
    if amount and amount > 0:
        qr_string += build_field(54, str(int(amount)))
    
    # Country Code
    qr_string += build_field(58, "VN")
    
    # Additional Data Field
    if description:
        additional_data = build_field(8, description)  # Purpose of transaction
        qr_string += build_field(62, additional_data)
    
    # CRC - phải tính sau khi đã có toàn bộ chuỗi
    qr_string += "6304"  # Field 63 (CRC) với length = 04
    crc = calculate_crc(qr_string)
    qr_string += crc
    
    return qr_string

# Generate QR Code service
def generate_qr_code_service(booking_id):
    try:
        account_id = get_jwt_identity()
        
        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404
        
        payment_type_param = request.args.get('payment_type', 'FULL')  # FULL or DEPOSIT
        amount_param = request.args.get('amount')
        
        if booking.status == BookingStatusEnum.DEPOSIT.value:
            # Đã đặt cọc, thanh toán phần còn lại
            amount = int(booking.remaining_amount)
            payment_type = "Thanh toán phần còn lại (60%)"
        else:
            if amount_param:
                amount = int(float(amount_param))
                if payment_type_param == 'DEPOSIT':
                    payment_type = "Đặt cọc (40%)"
                else:
                    payment_type = "Thanh toán 100%"
            elif payment_type_param == 'DEPOSIT':
                amount = int(booking.final_price * 0.4)
                payment_type = "Đặt cọc (40%)"
            else:
                amount = int(booking.final_price)
                payment_type = "Thanh toán 100%"

        # if booking.account_id != account_id:
        #     return jsonify({"message": "Sai tài khoản"}), 403

        # Thông tin ngân hàng
        bank_bin = "970422"  # MB Bank BIN code
        account_no = "88868668688668"
        account_name = "NGUYEN QUOC CUONG"
        description = booking.booking_code
        
        # Tạo chuỗi QR theo chuẩn VietQR (EMVCo)
        qr_content = build_vietqr_string(bank_bin, account_no, amount, description)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=None,  # Auto size
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return jsonify({
            "message": "Tạo mã QR thành công",
            "qr_code": f"data:image/png;base64,{img_base64}",
            "qr_content": qr_content,  
            "payment_type": payment_type,
            "bank_info": {
                "bank_name": "MB - Ngân hàng TMCP Quân Đội",
                "bank_bin": bank_bin,
                "account_no": account_no,
                "account_name": account_name,
                "amount": amount,
                "description": description
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi tạo QR code: {str(e)}")
        return jsonify({"message": "Lỗi khi tạo QR code", "error": str(e)}), 500
    
#get all payment admin
def get_all_payment_admin_service():
    try:
        payments = Payments.query.order_by(Payments.created_at.desc()).all()
        if not payments:
            return jsonify({"message":"Không có thanh toán nào trong hệ thống", "data":[]}),200
        return payments_schema.dump(payments),200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách thanh toán: {str(e)}"}), 500
    
#create payment admin
def create_payment_admin_service():
    try:
        data = request.form

        booking_id = data.get("booking_id")
        payment_method = data.get("payment_method")
        amount = data.get("amount")

        if not all([booking_id, payment_method, amount]):
            return jsonify({
                "message": "Thiếu thông tin: booking_id, payment_method, amount"
            }), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        if payment_method not in [e.value for e in PaymentMethodEnum]:
            return jsonify({"message": "Phương thức thanh toán không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        # TỰ ĐỘNG TÍNH TOÁN is_full_payment và remaining_amount
        final_price = float(booking.final_price)
        deposit_amount = final_price * 0.4
        
        diff_deposit = abs(amount - deposit_amount)
        diff_full = abs(amount - final_price)
        
        # Ưu tiên thanh toán đủ nếu gần với final_price
        if diff_full <= 1000:
            # Thanh toán 100%
            is_full_payment = 1
            remaining_amount = 0.0
        elif diff_deposit <= 1000:
            # Đặt cọc 40%
            is_full_payment = 0
            remaining_amount = final_price - amount
        else:
            return jsonify({
                "message": f"Số tiền không hợp lệ. Chọn: {int(deposit_amount):,}đ (đặt cọc 40%) hoặc {int(final_price):,}đ (thanh toán 100%)"
            }), 400

        new_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=amount,
            status=PaymentStatusEnum.COMPLETED.value,
        )

        db.session.add(new_payment)
        db.session.flush()

        files = request.files.getlist("images")
        uploaded_images = []

        if files and len(files) > 0 and files[0].filename != '':
            try:
                uploaded_images = create_payment_image(
                    new_payment.payment_id,
                    files
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "Upload ảnh thất bại",
                    "error": str(e)
                }), 400

        booking.paid_money = float(booking.paid_money) + amount
        booking.is_full_payment = is_full_payment  
        booking.remaining_amount = remaining_amount  
        booking.status = BookingStatusEnum.CONFIRMED.value

        schedule = Tour_Schedules.query.get(booking.schedule_id)

        if schedule:
            total_passengers = (
                booking.num_adults +
                booking.num_children +
                booking.num_infants
            )

            schedule.booked_seats += total_passengers

            if schedule.booked_seats >= schedule.available_seats:
                schedule.status = ScheduleStatusEnum.FULL.value

        db.session.commit()

        response_data = {
            "message": "Tạo thanh toán thành công",
            "payment_id": new_payment.payment_id,
            "booking_code": booking.booking_code,
            "is_full_payment": booking.is_full_payment,
            "paid_money": float(booking.paid_money),
            "remaining_amount": float(booking.remaining_amount)
        }

        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo thanh toán (admin): {str(e)}")
        return jsonify({
            "message": "Lỗi khi tạo thanh toán",
            "error": str(e)
        }), 500
    
def calculate_refund_amount(booking, payment_amount):
    """
    Tính toán số tiền hoàn lại cho một payment cụ thể
    Hàm này GIỮ NGUYÊN logic cũ, dùng cho trường hợp 1 payment
    """
    try:
        if not booking.schedule:
            return None
        
        departure_date = booking.schedule.departure_date
        
        cancellation_date = booking.cancelled_at if booking.cancelled_at else datetime.now()
        
        if isinstance(departure_date, datetime):
            departure_datetime = departure_date
        else:
            departure_datetime = datetime.combine(departure_date, datetime.min.time())
        
        days_before_departure = (departure_datetime - cancellation_date).days
        
        is_full_payment = bool(booking.is_full_payment)
        print("is_full_payment:", is_full_payment)
        
        if is_full_payment:
            if days_before_departure < 7:
                refund_percentage = 30
            else:
                refund_percentage = 70
        else:
            if days_before_departure >= 7:
                refund_percentage = 70
            elif days_before_departure >= 4:
                refund_percentage = 30
            else:
                refund_percentage = 0
        
        refund_amount = float(payment_amount) * (refund_percentage / 100)
        print("refund_amount:", refund_amount, "refund_percentage:", refund_percentage)
        
        return {
            "refund_amount": round(refund_amount, 2),
            "refund_percentage": refund_percentage,
            "days_before_departure": days_before_departure,
            "departure_date": departure_datetime.strftime("%Y-%m-%d"),
            "cancellation_date": cancellation_date.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        current_app.logger.error(f"Lỗi khi tính toán hoàn tiền: {str(e)}")
        return None

#read payment admin by uuid - GIỮ NGUYÊN LOGIC CŨ
def read_payment_detail_admin_service(payment_id):
    try:
        payment = Payments.query.get(payment_id)
        if not payment:
            return jsonify({"message": "Không tìm thấy thanh toán"}), 404
        
        payment_data = readPaymentDetailAdmin_schema.dump(payment)
        
        if payment.booking:
            payment_data['cancellation_reason'] = payment.booking.cancellation_reason
            
            if payment.booking.status in [BookingStatusEnum.CANCELLED, BookingStatusEnum.CANCEL_PENDING, BookingStatusEnum.CONFIRMED]:
                # GIỮ NGUYÊN: Tính refund cho payment này (logic cũ)
                refund_info = calculate_refund_amount(payment.booking, payment.amount)
                if refund_info:
                    payment_data['refund_info'] = refund_info
                else:
                    payment_data['refund_info'] = None
            else:
                payment_data['refund_info'] = None
        else:
            payment_data['cancellation_reason'] = None
            payment_data['refund_info'] = None
        
        return jsonify(payment_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy chi tiết thanh toán: {str(e)}")
        return jsonify({"message": "Lỗi hệ thống khi lấy chi tiết thanh toán", "error": str(e)}), 500

#read payment detail admin by booking_id - CẢI TIẾN ĐỂ XỬ LÝ NHIỀU PAYMENTS
def read_payment_detail_admin_by_booking_id_service(booking_id):
    try:
        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404
        
        # Lấy TẤT CẢ payments của booking
        all_payments = Payments.query.filter_by(booking_id=booking_id).order_by(Payments.created_at.desc()).all()
        
        if not all_payments:
            return jsonify({"message": "Không tìm thấy thanh toán cho booking này"}), 404
        
        payment_count = len(all_payments)
        
        # Nếu chỉ có 1 payment -> GIỮ NGUYÊN LOGIC CŨ
        if payment_count == 1:
            return read_payment_detail_admin_service(all_payments[0].payment_id)
        
        # Nếu có NHIỀU payments -> LOGIC MỚI
        # Tính tổng số tiền đã thanh toán
        total_paid = sum(float(p.amount) for p in all_payments)
        
        # Lấy payment mới nhất
        latest_payment = all_payments[0]
        payment_data = readPaymentDetailAdmin_schema.dump(latest_payment)
        
        payment_data['cancellation_reason'] = booking.cancellation_reason
        
        if booking.status in [BookingStatusEnum.CANCELLED, BookingStatusEnum.CANCEL_PENDING, BookingStatusEnum.CONFIRMED]:
            refund_info = calculate_refund_amount(booking, total_paid)
            if refund_info:
                refund_info['payment_count'] = payment_count
                refund_info['total_paid'] = round(total_paid, 2)
                refund_info['payment_breakdown'] = [
                    {
                        "payment_id": p.payment_id,
                        "amount": float(p.amount),
                        "payment_method": p.payment_method.value if hasattr(p.payment_method, 'value') else str(p.payment_method),
                        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else None
                    }
                    for p in all_payments
                ]
                payment_data['refund_info'] = refund_info
            else:
                payment_data['refund_info'] = None
        else:
            payment_data['refund_info'] = None
        
        return jsonify(payment_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy chi tiết thanh toán theo booking_id: {str(e)}")
        return jsonify({"message": "Lỗi hệ thống khi lấy chi tiết thanh toán", "error": str(e)}), 500

#create payment remaining admin
def create_payment_remaining_admin_service():
    try:
        data = request.form

        booking_id = data.get("booking_id")
        payment_method = data.get("payment_method")
        amount_str = data.get("amount")

        if not all([booking_id, payment_method, amount_str]):
            return jsonify({
                "message": "Thiếu thông tin: booking_id, payment_method, amount"
            }), 400

        try:
            amount = float(amount_str)
            if amount <= 0:
                return jsonify({"message": "Số tiền phải lớn hơn 0"}), 400
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        if payment_method not in [e.value for e in PaymentMethodEnum]:
            return jsonify({"message": "Phương thức thanh toán không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        if booking.is_full_payment:
            return jsonify({
                "message": "Booking đã thanh toán đầy đủ (is_full_payment: True), không thể tạo thêm thanh toán"
            }), 400

        remaining = float(booking.remaining_amount or 0)
        current_paid = float(booking.paid_money or 0)
        final_price = float(booking.final_price)

        if remaining <= 0:
            remaining = final_price - current_paid
            if remaining <= 0:
                return jsonify({"message": "Booking đã thanh toán đầy đủ, không thể tạo thêm thanh toán"}), 400

        if abs(amount - remaining) > 1000:
            return jsonify({
                "message": f"Số tiền không hợp lệ. Cần thanh toán phần còn lại: {int(remaining):,}đ"
            }), 400

        new_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=amount,
            status=PaymentStatusEnum.COMPLETED.value,
        )

        db.session.add(new_payment)
        db.session.flush()

        files = request.files.getlist("images")
        uploaded_images = []

        if files and len(files) > 0 and files[0].filename != '':
            try:
                uploaded_images = create_payment_image(
                    new_payment.payment_id,
                    files
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "Upload ảnh thất bại",
                    "error": str(e)
                }), 400

        booking.paid_money = float(current_paid) + amount
        booking.remaining_amount = 0.0
        booking.is_full_payment = True

        db.session.commit()

        response_data = {
            "message": "Thanh toán phần còn lại thành công",
            "payment_id": new_payment.payment_id,
        }

        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo thanh toán phần còn lại (admin): {str(e)}")
        return jsonify({
            "message": "Lỗi khi tạo thanh toán phần còn lại",
            "error": str(e)
        }), 500 

#create payment remaining user
def create_payment_remaining_user_service():
    try:
        data = request.form

        booking_id = data.get("booking_id")
        payment_method = data.get("payment_method")
        amount_str = data.get("amount")

        if not all([booking_id, payment_method, amount_str]):
            return jsonify({
                "message": "Thiếu thông tin: booking_id, payment_method, amount"
            }), 400

        try:
            amount = float(amount_str)
            if amount <= 0:
                return jsonify({"message": "Số tiền phải lớn hơn 0"}), 400
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        if payment_method not in [e.value for e in PaymentMethodEnum]:
            return jsonify({"message": "Phương thức thanh toán không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        if booking.is_full_payment:
            return jsonify({
                "message": "Booking đã thanh toán đầy đủ"
            }), 400

        remaining = float(booking.remaining_amount or 0)
        current_paid = float(booking.paid_money or 0)
        final_price = float(booking.final_price)

        if remaining <= 0:
            remaining = final_price - current_paid

        if remaining <= 0:
            return jsonify({
                "message": "Booking đã thanh toán đủ, không thể gửi thêm"
            }), 400

        if abs(amount - remaining) > 1000:
            return jsonify({
                "message": f"Số tiền không hợp lệ. Phần còn lại: {int(remaining):,}đ"
            }), 400

        new_payment = Payments(
            booking_id=booking_id,
            payment_method=payment_method,
            amount=amount,
            status=PaymentStatusEnum.BONUS.value  
        )

        db.session.add(new_payment)
        db.session.flush()

        files = request.files.getlist("images")
        uploaded_images = []

        if files and len(files) > 0 and files[0].filename != '':
            try:
                uploaded_images = create_payment_image(
                    new_payment.payment_id,
                    files
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "Upload ảnh thất bại",
                    "error": str(e)
                }), 400
            
        booking.is_bonus = True
        db.session.add(booking)

        db.session.commit()

        response_data = {
            "message": "Đã gửi yêu cầu thanh toán, đang chờ xác nhận",
            "payment_id": new_payment.payment_id,
            "status": PaymentStatusEnum.BONUS.value
        }

        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi tạo payment remaining user: {str(e)}")
        return jsonify({
            "message": "Lỗi khi gửi yêu cầu thanh toán",
            "error": str(e)
        }), 500