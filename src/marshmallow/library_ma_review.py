from src.extension import ma
from src.model.model_review import Reviews
from marshmallow import fields as ma_fields


class ReviewSchema(ma.SQLAlchemySchema):
    class Meta:
        model= Reviews
        load_instance = True    
        include_fk = True

    review_id = ma.auto_field()
    tour_id = ma.auto_field()
    booking_id = ma.auto_field()
    account_id = ma.auto_field()
    rating = ma.auto_field()
    comment = ma.auto_field()
    created_at = ma.auto_field()
    booking_code = ma_fields.Method("get_booking_code")
    
    def get_booking_code(self, obj):
        return obj.booking.booking_code if obj.booking else None

reviews_schema = ReviewSchema(many=True)