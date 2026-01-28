from marshmallow import fields as ma_fields
from src.extension import ma
from src.model.model_booking import Bookings
from src.marshmallow.library_ma_booking_passenger import ReadBookingPassengerSchema

class ReadBookingUserSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Bookings
        load_instance = True
        include_fk = True

    booking_id = ma.auto_field()
    booking_code = ma.auto_field()
    tour_id = ma.auto_field()
    schedule_id = ma.auto_field()
    coupon_id = ma.auto_field()
    num_adults = ma.auto_field()
    num_children = ma.auto_field()
    num_infants = ma.auto_field()
    total_price = ma.auto_field()
    discount_amount = ma.auto_field()
    final_price = ma.auto_field()
    paid_money = ma.auto_field()
    is_full_payment = ma.auto_field()
    is_bonus = ma.auto_field()
    contact_name = ma.auto_field()
    contact_email = ma.auto_field()
    contact_phone = ma.auto_field()
    contact_address = ma.auto_field()
    status = ma.auto_field()
    cancellation_reason = ma.auto_field()
    created_at = ma.auto_field()
    special_request = ma.auto_field()
    remaining_amount = ma.auto_field()
    tour_title = ma_fields.Function(lambda obj: obj.tour.title if obj.tour else None)
    depart_date = ma_fields.Function(lambda obj: obj.schedule.departure_date if obj.schedule else None)
    passengers = ma_fields.Nested(ReadBookingPassengerSchema, many=True)

read_one_booking_user_schema = ReadBookingUserSchema()
read_booking_user_schema = ReadBookingUserSchema(many=True)