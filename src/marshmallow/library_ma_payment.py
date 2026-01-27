from src.extension import ma
from src.marshmallow.library_ma_payment_images import PaymentImagesSchema
from src.model.model_payment import Payments
from marshmallow import fields as ma_fields

class PaymentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Payments
        load_instance = True 
        include_fk = True

    payment_id = ma.auto_field()
    booking_id = ma.auto_field()
    payment_method = ma.auto_field()
    amount = ma.auto_field()
    status = ma.auto_field()
    created_at = ma.auto_field()
    
    booking_code = ma_fields.Method("get_booking_code")
    
    def get_booking_code(self, obj):
        return obj.booking.booking_code if obj.booking else None

payments_schema = PaymentSchema(many=True)

class ReadPaymentDetailAdminSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Payments
        load_instance = True 
        include_fk = True

    payment_id = ma.auto_field()
    booking_id = ma.auto_field()
    payment_method = ma.auto_field()
    amount = ma.auto_field()
    status = ma.auto_field()
    created_at = ma.auto_field()
    updated_at = ma.auto_field()
    
    booking_code = ma_fields.Method("get_booking_code")
    payment_images = ma_fields.Nested(PaymentImagesSchema, many=True)
    money_paid = ma_fields.Method("get_paid_money")
    status_booking = ma_fields.Method("get_status_booking")
    
    def get_booking_code(self, obj):
        return obj.booking.booking_code if obj.booking else None
    
    def get_paid_money(self, obj):
        return float(obj.booking.paid_money) if obj.booking else 0
    
    def get_status_booking(self, obj):
        if obj.booking:
            status = obj.booking.status
            return status.value.upper() if hasattr(status, 'value') else str(status)
        return None

readPaymentDetailAdmin_schema = ReadPaymentDetailAdminSchema()
