from src.extension import ma
from src.model.model_tour import Tours

class TourSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tours
        load_instance = True
        include_fk = True

    tour_id = ma.auto_field()
    tour_code = ma.auto_field()
    title = ma.auto_field()
    duration_days = ma.auto_field()
    duration_nights = ma.auto_field()
    highlights = ma.auto_field()
    included_services = ma.auto_field()
    excluded_services = ma.auto_field()
    attractions = ma.auto_field()
    cuisine = ma.auto_field()
    suitable_for = ma.auto_field()
    ideal_time = ma.auto_field()
    transportation = ma.auto_field()
    promotions = ma.auto_field()
    depart_destination = ma.auto_field()
    base_price = ma.auto_field()
    child_price = ma.auto_field()
    infant_price = ma.auto_field()
    single_room_surcharge = ma.auto_field()
    main_image_url = ma.auto_field()
    main_image_public_id = ma.auto_field()
    rating_average = ma.auto_field()
    total_reviews = ma.auto_field()
    is_featured = ma.auto_field()
    is_active = ma.auto_field()
    created_by = ma.auto_field()
    created_at = ma.auto_field()
    updated_at = ma.auto_field()

tour_schema = TourSchema()

class TourInfoSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tours
        load_instance = True
        include_fk = True

    tour_id = ma.auto_field()
    tour_code = ma.auto_field()
    title = ma.auto_field()
    duration_days = ma.auto_field()
    duration_nights = ma.auto_field()
    depart_destination = ma.auto_field()
    base_price = ma.auto_field()
    main_image_url = ma.auto_field()
    rating_average = ma.auto_field()
    total_reviews = ma.auto_field()
    is_featured = ma.auto_field()
    is_active = ma.auto_field()
    created_at = ma.auto_field()
    transportation = ma.auto_field()

tourInfo_schema = TourInfoSchema()
tourInfos_schema = TourInfoSchema(many=True)
