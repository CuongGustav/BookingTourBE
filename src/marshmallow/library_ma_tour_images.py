from src.extension import ma
from src.model.model_tour_image import Tour_Images

class TourImageCreateSchema(ma.Schema):
    image_url = ma.Str(required=True)
    image_public_id = ma.Str(required=False)
    display_order = ma.Int(required=False)

tour_image_create_schema = TourImageCreateSchema()