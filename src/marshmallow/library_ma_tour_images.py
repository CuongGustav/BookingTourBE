from src.extension import ma
from src.model.model_tour_image import Tour_Images

class TourImageCreateSchema(ma.Schema):
    image_url = ma.Str(required=True)
    image_public_id = ma.Str(required=False)
    display_order = ma.Int(required=False)

tour_image_create_schema = TourImageCreateSchema()

class TourImageReadSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tour_Images
        load_instance = True
        include_fk = True

    tour_image_id = ma.auto_field()
    image_url = ma.auto_field()
    image_public_id = ma.auto_field()
    display_order = ma.auto_field()

tour_image_read_schema = TourImageReadSchema()
tour_images_read_schema = TourImageReadSchema(many=True)