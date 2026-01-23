from datetime import datetime
from flask import jsonify, request
from src.marshmallow.library_ma_account import AccountInfoSchema, AccountListSchema
from src.model.model_account import Accounts
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.extension import db
from src.common.decorators import require_role

account_info_schema = AccountInfoSchema()
account_list_schema = AccountListSchema(many=True)
account_info_detail_schema = AccountListSchema()

#get account by account_id
@jwt_required()
def get_all_information_account_service():
    account_id = get_jwt_identity()
    account = Accounts.query.filter_by(account_id=account_id).first()

    if not account:
        return {"message": "Không tìm thấy thông tin tài khoản"}, 404
    
    return account_info_schema.dump(account), 200


#change password
@jwt_required()
def change_password_service():
    data = request.get_json()
    current_password = data.get("password")
    new_password = data.get("new_password")
    account_id = get_jwt_identity()

    if not current_password or not new_password:
        return jsonify({"message": "Vui lòng cung cấp mật khẩu hiện tại và mật khẩu mới"}), 400

    account = Accounts.query.filter_by(account_id=account_id).first()

    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}), 404

    if not account.check_password(current_password):
        return jsonify({"message": "Mật khẩu hiện tại không đúng"}), 400

    account.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Đổi mật khẩu thành công"}), 200

#update account
@jwt_required()
def update_information_account_service():
    try:
        account_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({"message": "Không có dữ liệu gửi lên"}), 400

        account = Accounts.query.filter_by(account_id=account_id).first()
        if not account:
            return jsonify({"message": "Không tìm thấy tài khoản"}), 404

        email = data.get("email")
        if email and email != account.email:
            existed_email = Accounts.query.filter(
                Accounts.email == email,
                Accounts.account_id != account_id
            ).first()

            if existed_email:
                return jsonify({"message": "Email đã tồn tại"}), 400

        phone = data.get("phone")
        if phone and phone != account.phone:
            existed_phone = Accounts.query.filter(
                Accounts.phone == phone,
                Accounts.account_id != account_id
            ).first()

            if existed_phone:
                return jsonify({"message": "Số điện thoại đã tồn tại"}), 400

        cccd = data.get("cccd")
        if cccd and cccd != account.cccd:
            existed_cccd = Accounts.query.filter(
                Accounts.cccd == cccd,
                Accounts.account_id != account_id
            ).first()

            if existed_cccd:
                return jsonify({"message": "CCCD đã tồn tại"}), 400

        allowed_fields = {"full_name", "email", "phone", "address", "gender", "cccd", "date_of_birth"}

        updated = False

        for field in allowed_fields:
            if field in data:
                value = data[field]
                if value is not None and str(value).strip() != "":
                    setattr(account, field, value)
                    updated = True

        if not updated:
            return jsonify({"message": "Không có thông tin nào được cập nhật"}), 400

        db.session.commit()
        return jsonify({"message": "Cập nhật thông tin thành công"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Cập nhật thất bại: {str(e)}"}), 500

    
#delete soft account user
@jwt_required()
def delete_soft_account_user_service():
    account_id = get_jwt_identity()
    data = request.get_json()

    if not data:
        return jsonify({"message": "Không có dữ liệu gửi lên"}), 400

    account = Accounts.query.filter_by(account_id=account_id).first()
    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}), 404
    
    is_active = data.get("is_active")
    if is_active is None:
        return jsonify({"message": "Thiếu thông tin is_active"}), 400
    account.is_active = bool(is_active)
    account.updated_at = datetime.now()
    db.session.commit()

    return jsonify({"message": f"Tài khoản đã được xóa thành công"}), 200

#get all account admin
@require_role('qcadmin')
def get_all_account_service():
    try:
        accounts = Accounts.query.order_by(Accounts.created_at.desc()).all()
        if not accounts:
            return jsonify ({"message":"Không có tài khoản nào", "data": []}), 200
        return account_list_schema.dump(accounts),200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách tài khoản: {str(e)}"}), 500
    
#get account by account_id admin
@require_role('qcadmin')
def get_account_by_uuid_admin_service(account_id):
    if not account_id:
        return jsonify({"message": "Thiếu thông tin account_id"}), 400

    account = Accounts.query.filter_by(account_id=account_id).first()
    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}), 404

    return account_info_detail_schema.dump(account), 200

#update account by admin
@require_role('qcadmin')
def update_account_admin_service():
    data = request.get_json()
    if not data:
        return jsonify({"message":"Không có dữ liệu gửi lên"}),400
    
    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"message": "Thiếu account_id"}),400
    
    account = Accounts.query.filter_by(account_id=account_id).first()
    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}),404
    
    allowed_fields = {
        "full_name", "email", "phone", "address", "gender", "cccd", "date_of_birth", "role_account", "status", "is_active"
    }
    updated = False

    for field in allowed_fields:
        if field in data:
            value = data[field]
            if value is not None and str(value).strip() != "":
                setattr(account, field, value)
                updated = True

    if not updated:
        return jsonify({"message": "Không có thông tin nào được cập nhật"}), 400
    
    try:
        db.session.commit()
        return jsonify({"message": "Cập nhật thông tin tài khoản thành công"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Cập nhật thất bại, vui lòng thử lại. Lỗi: {str(e)}"}), 500
    
#delete soft admin
@require_role('qcadmin')
def delete_soft_account_admin_service():
    data = request.get_json()
    if not data:
        return jsonify({"message":"Không có dữ liệu gửi lên"}),400

    account_id = data.get("account_id")
    if not account_id:
        return jsonify({"message": "Thiếu account_id"}),400
    
    account = Accounts.query.filter_by(account_id=account_id).first()
    if not account:
        return jsonify({"message": "Không tìm thấy tài khoản"}),404
    
    is_active = data.get("is_active")
    if is_active is None:
        return jsonify({"message": "Thiếu thông tin is_active"}), 400
    account.is_active = bool(is_active)
    account.updated_at = datetime.now()

    db.session.commit()

    status_msg = "kích hoạt" if account.is_active else "khóa/xóa mềm"
    return jsonify({"message": f"Tài khoản đã được {status_msg} thành công"}), 200
