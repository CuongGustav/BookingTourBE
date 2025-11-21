from flask import request
from src.marshmallow.library_ma_account import AccountInfoSchema
from src.model.model_account import Accounts
from flask_jwt_extended import get_jwt_identity, jwt_required

account_info_schema = AccountInfoSchema()

@jwt_required()
def get_all_information_account_service():
    account_id = get_jwt_identity()
    account = Accounts.query.filter_by(account_id=account_id).first()

    if not account:
        return {"message": "Không tìm thấy thông tin tài khoản"}, 404
    
    return account_info_schema.dump(account), 200