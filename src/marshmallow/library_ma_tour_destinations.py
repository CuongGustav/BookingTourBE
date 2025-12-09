from src.extension import ma
from src.model.model_tour_destination import Tour_Destinations

class TourDestinationsSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tour_Destinations
        load_instance = True
        include_fk = True

    id = ma.auto_field()
    tour_id = ma.auto_field()
    destination_id = ma.auto_field()

tour_destinations_schema = TourDestinationsSchema(many=True)