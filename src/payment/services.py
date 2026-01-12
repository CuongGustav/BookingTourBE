from flask import request, jsonify, current_app
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from src.model.model_payment import Payments, PaymentMethodEnum, PaymentStatusEnum
from src.model.model_booking import Bookings, BookingStatusEnum
from datetime import datetime
from src.payment_images.services import create_payment_image
import qrcode
import io
import base64
import crc16
from src.marshmallow.library_ma_payment import payments_schema, readPaymentDetailAdmin_schema

#create payment service
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

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

        if booking.account_id != account_id:
            return jsonify({"message": "Sai tài khoản"}), 403

        if booking.status != BookingStatusEnum.PENDING:
            return jsonify({"message": "Booking không phải ở trạng thái đang xử lý"}), 400

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
                uploaded_images = create_payment_image(new_payment.payment_id, files)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "upload ảnh thất bại",
                    "error": str(e)
                }), 400

        booking.status = BookingStatusEnum.PAID.value
        
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

        # if booking.account_id != account_id:
        #     return jsonify({"message": "Sai tài khoản"}), 403

        # Thông tin ngân hàng
        bank_bin = "970422"  # MB Bank BIN code
        account_no = "88868668688668"
        account_name = "NGUYEN QUOC CUONG"
        amount = int(booking.final_price)
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
            return jsonify({"message": "Thiếu thông tin: booking_id, payment_method, amount"}), 400

        try:
            amount = float(amount)
        except ValueError:
            return jsonify({"message": "Số tiền không hợp lệ"}), 400

        if payment_method not in [e.value for e in PaymentMethodEnum]:
            return jsonify({"message": "Phương thức thanh toán không hợp lệ"}), 400

        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404

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
                uploaded_images = create_payment_image(new_payment.payment_id, files)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "Upload ảnh thất bại",
                    "error": str(e)
                }), 400

        booking.status = BookingStatusEnum.CONFIRMED.value
        
        from src.model.model_tour_schedule import Tour_Schedules
        schedule = Tour_Schedules.query.get(booking.schedule_id)
        if schedule:
            total_passengers = booking.num_adults + booking.num_children + booking.num_infants
            schedule.booked_seats += total_passengers
            
            if schedule.booked_seats >= schedule.available_seats:
                from src.model.model_tour_schedule import ScheduleStatusEnum
                schedule.status = ScheduleStatusEnum.FULL.value
        
        db.session.commit()

        response_data = {
            "message": "Tạo thanh toán thành công",
            "payment_id": new_payment.payment_id,
            "booking_code": booking.booking_code
        }
        
        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo thanh toán (admin): {str(e)}")
        return jsonify({"message": "Lỗi khi tạo thanh toán", "error": str(e)}), 500
    
#read payment admin by uuid
def read_payment_detail_admin_service(payment_id):
    try:
        payment = Payments.query.get(payment_id)
        if not payment:
            return jsonify({"message": "Không tìm thấy thanh toán"}), 404
        
        return jsonify(readPaymentDetailAdmin_schema.dump(payment)), 200
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy chi tiết thanh toán: {str(e)}")
        return jsonify({"message": "Lỗi hệ thống khi lấy chi tiết thanh toán", "error": str(e)}), 500
    
#read payment detail admin by booking_id
def read_payment_detail_admin_by_booking_id_service(booking_id):
    try:
        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404
        
        if booking.status != BookingStatusEnum.PAID:
            return jsonify({"message": "Booking chưa được thanh toán"}), 400
        
        payment = Payments.query.filter_by(booking_id=booking_id).first()
        if not payment:
            return jsonify({"message": "Không tìm thấy thanh toán cho booking này"}), 404
        
        return read_payment_detail_admin_service(payment.payment_id)
        
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy chi tiết thanh toán theo booking_id: {str(e)}")
        return jsonify({"message": "Lỗi hệ thống khi lấy chi tiết thanh toán", "error": str(e)}), 500


        