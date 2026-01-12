from src.extension import ma
from src.model.model_payment_image import PaymentImages

class PaymentImagesSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PaymentImages
        load_instance = True 
        include_fk = True

    image_id = ma.auto_field()
    payment_id = ma.auto_field()
    image_url = ma.auto_field()
    uploaded_at = ma.auto_field()

payment_image_schema = PaymentImagesSchema()