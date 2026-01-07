from marshmallow import fields as ma_fields
from src.extension import ma
from src.model.model_booking import Bookings

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
    contact_name = ma.auto_field()
    contact_email = ma.auto_field()
    contact_phone = ma.auto_field()
    contact_address = ma.auto_field()
    status = ma.auto_field()
    cancellation_reason = ma.auto_field()
    created_at = ma.auto_field()
    special_request = ma.auto_field()
    tour_title = ma_fields.Function(lambda obj: obj.tour.title if obj.tour else None)
read_booking_user_schema = ReadBookingUserSchema(many=True)