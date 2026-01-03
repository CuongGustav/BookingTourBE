from src.extension import ma
from src.model.model_tour_schedule import Tour_Schedules

class TourScheduleCreateSchema(ma.Schema):
    departure_date = ma.Date(required=True)
    return_date = ma.Date(required=True)
    available_seats = ma.Int(required=True)
    price_adult = ma.Decimal(required=True)
    price_child = ma.Decimal(required=False)
    price_infant = ma.Decimal(required=False)

tour_schedule_create_schema = TourScheduleCreateSchema()

class TourScheduleSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Tour_Schedules
        load_instance = True

    schedule_id = ma.auto_field()
    departure_date = ma.auto_field()
    return_date = ma.auto_field()
    available_seats = ma.auto_field()
    booked_seats = ma.auto_field()
    price_adult = ma.auto_field()
    price_child = ma.auto_field()
    price_infant = ma.auto_field()
    status = ma.auto_field()
    
tour_schedule_schema = TourScheduleSchema(many=True)
tour_schedule_detail_schema = TourScheduleSchema()

class TourScheduleUpdateSchema(ma.Schema):
    schedule_id = ma.Str(allow_none=True, dump_default=None) 
    departure_date = ma.Date(required=True)
    return_date = ma.Date(required=True)
    available_seats = ma.Int(required=True)
    price_adult = ma.Decimal(required=True)
    price_child = ma.Decimal(required=False, allow_none=True)
    price_infant = ma.Decimal(required=False, allow_none=True)

tour_schedule_update_schema = TourScheduleUpdateSchema()