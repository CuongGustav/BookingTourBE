from datetime import datetime, timedelta
from flask import make_response, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash
from src.extension import db
from src.library_ma import AccountSchema
from src.model import Accounts, ProviderEnum, GenderEnum
from src.extension import redis_blocklist

account_schema = AccountSchema()

# Register account 
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

# Login account user
def login_account_user_service():
    data = request.get_json()

    if not data:
        return jsonify({"Message":"Dữ liệu không hợp lệ"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Thiếu thông tin"}), 400
    
    account = Accounts.query.filter_by(email=email).first()
    if not account:
        return jsonify({"message": "Email không tồn tại"}),404
    if not account.check_password(password):
        return jsonify({"message":"Mật khẩu không đúng"}), 401
    if not account.is_active:
        return jsonify({"message":"Tài khoản đã bị khóa"}), 403
    
    #Create JWT Token
    access_token = create_access_token(
        identity=account.account_id,
        expires_delta=timedelta(hours=24),
        additional_claims={
            "role": account.role_account.value,
            "provider": account.provider.value
        }
    )
    refresh_token = create_refresh_token(identity=account.account_id)

    resp = make_response({
        "message": "Đăng nhập thành công",
        "user": {
            "account_id": account.account_id,
            "email": account.email,
            "full_name": account.full_name
        }
    })

    #Save token in cookie 
    resp.set_cookie("access_token", access_token, httponly=True, secure=False, samesite="Lax", max_age=86400)
    resp.set_cookie("refresh_token", refresh_token, httponly=True, secure=False, samesite="Lax", max_age=604800)

    return jsonify({
        "message": "Đăng nhập thành công",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "account_id": account.account_id,
            "email": account.email,
            "full_name": account.full_name
        }
    }), 200

#Get current user service
@jwt_required()
def get_current_user_service():
    account_id = get_jwt_identity()
    account = Accounts.query.get(account_id)
    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}), 404
    return account_schema.jsonify(account), 200
    
@jwt_required()
def logout_account_user_service():
    jwt_data = get_jwt()
    jti = jwt_data["jti"]
    exp_timestamp = jwt_data["exp"]

    now = datetime.utcnow()
    seconds_until_exp = int(exp_timestamp - now.timestamp())

    redis_blocklist.setex(jti, seconds_until_exp, "revoked")

    resp = make_response(jsonify({"message": "Đăng xuất thành công"}), 200)
    resp.set_cookie("access_token", "", expires=0)
    resp.set_cookie("refresh_token", "", expires=0)

    return resp