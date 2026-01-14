from src.extension import ma
from src.model.model_review_image import ReviewImages

class ReviewSchema(ma.SQLAlchemySchema):
    class Meta:
        model= ReviewImages
        load_instance = True    
        include_fk = True

    image_id = ma.auto_field()
    review_id = ma.auto_field()
    image_url = ma.auto_field()
    image_public_id = ma.auto_field()
    created_at = ma.auto_field()