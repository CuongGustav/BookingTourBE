from src.extension import ma
from src.model import Accounts

class AccountSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Accounts
        load_instance = True  

    account_id = ma.auto_field()
    email = ma.auto_field()
    full_name = ma.auto_field()
    phone = ma.auto_field()
    date_of_birth =  ma.auto_field() 
    gender = ma.auto_field()
    address = ma.auto_field()
    role_account = ma.auto_field()
