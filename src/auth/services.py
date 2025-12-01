from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import make_response, request, jsonify, redirect
from flask_jwt_extended import (create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required, 
                                set_access_cookies, set_refresh_cookies, unset_jwt_cookies)
from werkzeug.security import generate_password_hash, check_password_hash
from src.extension import db, redis_blocklist
from src.marshmallow.library_ma_account import AccountSchema
from src.model.model_account import Accounts, ProviderEnum, GenderEnum
from src.extension import redis_blocklist
import os
import requests
from src.common.decorators import require_role

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
    cccd = data.get("cccd")

    if not email or not password or not full_name or not cccd:
        return jsonify({"message": "Thiếu thông tin bắt buộc"}), 400

    # check email
    if Accounts.query.filter_by(email=email).first():
        return jsonify({"message": "Email đã được đăng ký"}), 400
    # check phone
    if phone and Accounts.query.filter_by(phone=phone).first():
        return jsonify({"message": "Số điện thoại đã được đăng ký"}), 400
    # check cccd
    if cccd and Accounts.query.filter_by(cccd=cccd).first():
        return jsonify({"message": "CCCD/CMND đã được đăng ký"}), 400
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
        address=address,
        cccd=cccd,
    )

    db.session.add(new_account)
    db.session.commit()

    return jsonify({"message": "Đã đăng ký tài khoản thành công."}), 201

# Login account user
def login_account_user_service():
    data = request.get_json()

    if not data:
        return jsonify({"Message":"Dữ liệu không hợp lệ"}), 400

    email_or_phone = data.get("email")
    password = data.get("password")

    if not email_or_phone or not password:
        return jsonify({"message": "Thiếu thông tin"}), 400
    
    account = Accounts.query.filter(
        (Accounts.email == email_or_phone) | (Accounts.phone == email_or_phone)
    ).first()
    if not account: 
        return jsonify({"message": "Email không tồn tại"}),404
    if not account.check_password(password):
        return jsonify({"message":"Mật khẩu không đúng"}), 401
    if not account.is_active:
        return jsonify({"message":"Tài khoản đã bị khóa"}), 403
    
    if account.role_account.value != 'qcuser':
        return jsonify({
            "message": "Vui lòng sử dụng trang đăng nhập dành cho quản trị viên"
        }), 403
    
    #Create JWT Token
    access_token = create_access_token(
        identity=account.account_id,
        expires_delta=timedelta(hours=24),
        additional_claims={
            "role": account.role_account.value,
            "provider": account.provider.value
        }
    )
    refresh_token = create_refresh_token(
        identity=account.account_id,
        expires_delta=timedelta(days=7)
    )

    resp = make_response({
        "message": "Đăng nhập thành công",
        "user": {
            "account_id": account.account_id,
            "email": account.email,
            "full_name": account.full_name,
            "phone": account.phone,
            "role_account": account.role_account.value,
            "access_token": access_token,  
        }
    })

    # Set JWT cookie
    set_access_cookies(resp, access_token, max_age=86400)
    set_refresh_cookies(resp, refresh_token, max_age=604800)

    return resp, 200

#Get current user service
@jwt_required()
@require_role('qcuser')
def get_current_user_service():
    account_id = get_jwt_identity()
    account = Accounts.query.get(account_id)
    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}), 404
    return account_schema.jsonify(account), 200

#Refresh token
@jwt_required(refresh=True)
def refresh_token_service():
    """Làm mới access token bằng refresh token"""
    identity = get_jwt_identity()
    claims = get_jwt()
    
    # Take role from token old
    role = claims.get("role", "user")
    is_admin = claims.get("is_admin", False)
    
    # Create token new with claims
    additional_claims = {
        "role": role,
        "provider": claims.get("provider", "local")
    }
    
    if is_admin:
        additional_claims["is_admin"] = True
        expires_delta = timedelta(hours=12)
        max_age = 43200
    else:
        expires_delta = timedelta(hours=24)
        max_age = 86400
    
    access_token = create_access_token(
        identity=identity,
        expires_delta=expires_delta,
        additional_claims=additional_claims
    )
    
    resp = make_response(jsonify({"message": "Access token mới đã được cấp"}))
    set_access_cookies(resp, access_token, max_age=max_age)
    
    return resp, 200

#Login admin
def login_account_admin_service():
    data = request.get_json()

    if not data:
        return jsonify({"message": "Dữ liệu không hợp lệ"}), 400
    
    email_or_phone = data.get("email")
    password = data.get("password")

    if not email_or_phone or not password:
        return jsonify({"message":"Thiếu thông tin đăng nhập"}), 400
    
    account = Accounts.query.filter(
        (Accounts.email == email_or_phone) | (Accounts.phone == email_or_phone)
    ).first()

    if not account:
        return jsonify({"message": "Email hoặc số điện thoại không tồn tại"}), 404
    if not account.check_password(password):
        return jsonify({"message":"Mật khẩu không đúng"}), 401
    if not account.is_active:
        return jsonify({"message":"Tài khoản đã bị khóa"}), 403
    
    if account.role_account.value != 'qcadmin':
        return jsonify({"message":"Bạn không có quyền truy cập trang quản trị"}), 403
    
    access_token = create_access_token(
        identity=account.account_id,
        expires_delta=timedelta(hours=12),
        additional_claims={
            "role": account.role_account.value,
            "provider": account.provider.value,
            "is_admin": True
        }
    )
    refresh_token = create_refresh_token(
        identity=account.account_id,
        expires_delta=timedelta(days=7)
    )
    resp = make_response({
        "message": "Đăng nhập quản trị thành công",
        "admin": {
            "account_id": account.account_id,
            "email": account.email,
            "full_name": account.full_name,
            "phone": account.phone,
            "role": account.role_account.value,
            "access_token": access_token
        }
    })

    set_access_cookies(resp, access_token, max_age=43200)  # 12 hours
    set_refresh_cookies(resp, refresh_token, max_age=604800)  # 7 days

    return resp, 200

# get current account admin
@require_role('qcadmin')
def get_current_admin_service(verified_account):
    return account_schema.jsonify(verified_account), 200

#Logout
@jwt_required()
def logout_account_service():
    jwt_data = get_jwt()
    jti = jwt_data["jti"]
    exp_timestamp = jwt_data["exp"]
    seconds_until_exp = int(exp_timestamp - datetime.now(timezone.utc).timestamp())

    redis_blocklist.setex(jti, seconds_until_exp, "revoked")
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        try:
            decoded_refresh = get_jwt(refresh_token)
            jti_refresh = decoded_refresh["jti"]
            exp_refresh = decoded_refresh["exp"]
            seconds_refresh = int(exp_refresh - datetime.utcnow().timestamp())
            redis_blocklist.setex(jti_refresh, seconds_refresh, "revoked")
        except Exception:
            pass

    resp = make_response(jsonify({"message": "Đăng xuất thành công"}))
    unset_jwt_cookies(resp)  # Delete cookie access + refresh

    return resp, 200

# Google OAuth Services
IS_PRODUCTION = os.getenv("FLASK_ENV") == "production"

# goole login service
def google_login_service():
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = f"{google_auth_url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&response_type={params['response_type']}&scope={params['scope']}&access_type={params['access_type']}&prompt={params['prompt']}"
    return jsonify({"auth_url": auth_url}), 200

# google callback service
def google_callback_service():
    code = request.args.get("code")
    if not code:
        return jsonify({"message": "Không nhận được mã xác thực từ Google"}), 400

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code"
    }

    try:
        token_response = requests.post(token_url, data=token_data, verify=IS_PRODUCTION)
        token_response.raise_for_status()
        tokens = token_response.json()
        access_token = tokens.get("access_token")

        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        user_info_response = requests.get(user_info_url, headers=headers, verify=IS_PRODUCTION)
        user_info_response.raise_for_status()
        user_info = user_info_response.json()

        google_id = user_info.get("id")
        email = user_info.get("email")
        full_name = user_info.get("name")

        if not email or not google_id:
            return jsonify({"message": "Không thể lấy thông tin từ Google"}), 400

        account = Accounts.query.filter_by(email=email).first()
        if account:
            if not account.google_id:
                account.google_id = google_id
                if account.provider == ProviderEnum.LOCAL.value:
                    account.provider = ProviderEnum.GOOGLE.value
                db.session.commit()
        else:
            random_password = generate_password_hash(os.urandom(24).hex())
            account = Accounts(
                email=email,
                password_hash=random_password,
                full_name=full_name,
                google_id=google_id,
                provider=ProviderEnum.GOOGLE.value,
                role_account="qcuser",
                is_active=True
            )
            db.session.add(account)
            db.session.commit()

        if not account.is_active:
            return redirect("http://127.0.0.1:3000/auth/login?error=locked")

        jwt_access_token = create_access_token(
            identity=account.account_id,
            expires_delta=timedelta(hours=24),
            additional_claims={
                "role": account.role_account.value,
                "provider": account.provider.value
            }
        )
        jwt_refresh_token = create_refresh_token(
            identity=account.account_id,
            expires_delta=timedelta(days=7)
        )

        resp = make_response(redirect("http://127.0.0.1:3000?login=success"))
        set_access_cookies(resp, jwt_access_token, max_age=86400)
        set_refresh_cookies(resp, jwt_refresh_token, max_age=604800)
        return resp

    except requests.exceptions.RequestException as e:
        return jsonify({"message": f"Lỗi SSL khi kết nối với Google: {str(e)}"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Lỗi xử lý đăng nhập: {str(e)}"}), 500