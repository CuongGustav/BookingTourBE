from src.extension import ma
from src.model.model_booking_passenger import BookingPassengers

class ReadBookingPassengerSchema(ma.SQLAlchemySchema):
    class Meta:
        model = BookingPassengers
        load_instance = True
        include_fk = True

    passenger_id = ma.auto_field()
    passenger_type = ma.auto_field()
    full_name = ma.auto_field()
    date_of_birth = ma.auto_field()
    gender = ma.auto_field()
    id_number = ma.auto_field()
    single_room = ma.auto_field()
    created_at = ma.auto_field()

read_booking_passenger_schema = ReadBookingPassengerSchema(many=True)