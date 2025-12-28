from src.extension import ma
from src.model.model_coupon import Coupons

class ReadCouponAdminSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Coupons
        load_instance = True
        include_fk = True
    
    coupon_id = ma.auto_field()
    code = ma.auto_field()
    description = ma.auto_field()
    discount_type = ma.auto_field()
    discount_value = ma.auto_field()
    min_order_amount = ma.auto_field()
    max_discount_amount = ma.auto_field()
    usage_limit = ma.auto_field()
    used_count = ma.auto_field()
    valid_from = ma.auto_field()
    valid_to = ma.auto_field()
    is_active = ma.auto_field()
    created_by = ma.auto_field()
    created_at = ma.auto_field()
    updated_at = ma.auto_field()
    image_coupon_url = ma.auto_field()
    image_coupon_public_id = ma.auto_field()

coupon_schema = ReadCouponAdminSchema()
coupons_schema = ReadCouponAdminSchema(many=True)

class ReadCouponImageSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Coupons
        load_instance = True
        include_fk = True
    
    image_coupon_url = ma.auto_field()

readCouponImages_schema = ReadCouponImageSchema(many=True)