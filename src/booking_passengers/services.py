from src.extension import db
from src.model.model_booking_passenger import BookingPassengers

def create_booking_passenger_service(
    booking_id: str,
    passenger_type: str,
    full_name: str,
    date_of_birth: str = None,
    gender: str = None,
    id_number: str = None,
    single_room: bool = False
):
    passenger = BookingPassengers(
        booking_id=booking_id,
        passenger_type=passenger_type,  
        full_name=full_name,
        date_of_birth=date_of_birth,
        gender=gender, 
        id_number=id_number,
        single_room=single_room
    )
    db.session.add(passenger)
    return passenger