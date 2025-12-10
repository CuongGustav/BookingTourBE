from src.extension import ma

class TourScheduleCreateSchema(ma.Schema):
    departure_date = ma.Date(required=True)
    return_date = ma.Date(required=True)
    available_seats = ma.Int(required=True)
    price_adult = ma.Decimal(required=True)
    price_child = ma.Decimal(required=False)
    price_infant = ma.Decimal(required=False)

tour_schedule_create_schema = TourScheduleCreateSchema()