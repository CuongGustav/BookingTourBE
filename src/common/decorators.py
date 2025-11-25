from functools import wraps
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from flask import jsonify
from src.model.model_account import Accounts


def require_role(required_role: str):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt()
            token_role = claims.get("role")

            if token_role != required_role:
                return jsonify({"message": f"Yêu cầu quyền {required_role}"}), 403

            account_id = get_jwt_identity()
            account = Accounts.query.get(account_id)

            if not account:
                return jsonify({"message": "Tài khoản không tồn tại"}), 404

            if not account.is_active:
                return jsonify({"message": "Tài khoản đã bị khóa"}), 403

            if account.role_account.value != required_role:
                return jsonify({"message": "Quyền truy cập không hợp lệ"}), 403

            if "verified_account" in fn.__code__.co_varnames:
                kwargs["verified_account"] = account

            return fn(*args, **kwargs)

        return decorator
    return wrapper
