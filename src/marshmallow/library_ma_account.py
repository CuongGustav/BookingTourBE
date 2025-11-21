from src.extension import ma
from src.model.model_account import Accounts
from src.model.model_booking import Bookings

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
    cccd = ma.auto_field()
    role_account = ma.auto_field()

class AccountInfoSchema(ma.SQLAlchemySchema):
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
    cccd = ma.auto_field()
    role_account = ma.auto_field()
    
    tour_booked = ma.Method("get_tour_booked")

    def get_tour_booked(self, obj):
        return Bookings.query.filter_by(account_id=obj.account_id, status='completed').count()
