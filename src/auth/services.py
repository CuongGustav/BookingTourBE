from flask import request, jsonify
from werkzeug.security import generate_password_hash
from src.extension import db
from src.library_ma import AccountSchema
from src.model import Accounts, ProviderEnum, GenderEnum

account_schema = AccountSchema()

# Register account service
def register_account_service():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Dữ liệu không hợp lệ"}), 400

    email = data.get("email")
    full_name = data.get("full_name")  
    phone = data.get("phone")
    password = data.get("password")
    date_of_birth = data.get("date_of_birth")
    address = data.get("address")
    provider_raw = data.get("provider", "local")  
    gender_raw = data.get("gender")

    if not email or not password or not full_name:
        return jsonify({"message": "Thiếu thông tin bắt buộc"}), 400

    # check email
    if Accounts.query.filter_by(email=email).first():
        return jsonify({"message": "Email đã được đăng ký"}), 400
    # check phone
    if phone and Accounts.query.filter_by(phone=phone).first():
        return jsonify({"message": "Số điện thoại đã được đăng ký"}), 400

    # Convert provider string sang Enum
    try:
        provider_enum = ProviderEnum(provider_raw)
    except ValueError:
        provider_enum = ProviderEnum.LOCAL 
    # Convert gender string sang Enum
    gender_enum = None
    if gender_raw:
        try:
            gender_enum = GenderEnum(gender_raw)
        except ValueError:
            gender_enum = None

    # Hash password
    password_hash = generate_password_hash(password)

    new_account = Accounts(
        email=email,
        password_hash=password_hash,
        full_name=full_name,
        provider=provider_enum,
        phone=phone,
        date_of_birth=date_of_birth,
        gender=gender_enum,
        address=address
    )

    db.session.add(new_account)
    db.session.commit()

    return jsonify({"message": "Đã đăng ký tài khoản thành công."}), 201
