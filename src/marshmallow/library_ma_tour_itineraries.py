from src.extension import ma
from src.model.model_tour_itinerary import Tour_Itineraries

class TourItineraryCreateSchema(ma.Schema):
    title = ma.Str(required=True)
    description = ma.Str(required=False)
    meals = ma.Str(required=False)
    display_order = ma.Int(required=False)

class TourItinerariesSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tour_Itineraries
        load_instance = True
        include_fk = True

    itinerary_id = ma.auto_field()
    tour_id = ma.auto_field()
    title = ma.auto_field()
    description = ma.auto_field()
    meals = ma.auto_field()
    display_order = ma.auto_field()
    created_at = ma.auto_field()
    updated_at = ma.auto_field()

tour_itinerary_create_schema = TourItineraryCreateSchema()
tour_itineraries_response_schema = TourItinerariesSchema(many=True)

class TourItineraryReadSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tour_Itineraries
        load_instance = True
        include_fk = True

    title = ma.auto_field()
    description = ma.auto_field()
    meals = ma.auto_field()
    display_order = ma.auto_field()

tour_itineraries_read_schema = TourItineraryReadSchema(many=True)