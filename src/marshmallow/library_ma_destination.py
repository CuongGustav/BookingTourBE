from src.extension import ma
from src.model.model_destination import Destinations

class DestinationSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Destinations
        load_instance = True
        include_fk = True

    destination_id = ma.auto_field()
    name = ma.auto_field()
    country = ma.auto_field()
    region = ma.auto_field()
    description = ma.auto_field()
    image_url = ma.auto_field()
    image_public_id = ma.auto_field()
    is_active = ma.auto_field()
    created_at = ma.auto_field()

destination_schema = DestinationSchema()
destinations_schema = DestinationSchema(many=True)

class DestinationRegionSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Destinations
        load_instance = True
        include_fk = True

    destination_id = ma.auto_field()
    name = ma.auto_field()
    image_url = ma.auto_field()
    image_public_id = ma.auto_field()

destinationRegions_schema = DestinationRegionSchema(many=True)

class DestinationCreateTourSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Destinations
        load_instance = True
        include_fk = True

    destination_id = ma.auto_field()
    name = ma.auto_field()

destinationCreateTour_schema = DestinationCreateTourSchema(many=True)