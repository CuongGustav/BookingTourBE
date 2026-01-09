from flask import jsonify
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

def update_booking_passengers_service(booking_id, passengers_data, num_adults, num_children, num_infants):
    try:
        BookingPassengers.query.filter_by(booking_id=booking_id).delete()
        db.session.flush()

        actual_adults = sum(1 for p in passengers_data if p["passenger_type"].lower() == "adult")
        actual_children = sum(1 for p in passengers_data if p["passenger_type"].lower() == "child")
        actual_infants = sum(1 for p in passengers_data if p["passenger_type"].lower() == "infant")
        if (actual_adults != num_adults or
            actual_children != num_children or
            actual_infants != num_infants):
            return jsonify({"message": "Số lượng hành khách không khớp"}), 400

        num_single_rooms = sum(1 for p in passengers_data if p.get("single_room", False))

        for passenger_data in passengers_data:
            create_booking_passenger_service(
                booking_id=booking_id,
                passenger_type=passenger_data["passenger_type"].upper(),
                full_name=passenger_data["full_name"],
                date_of_birth=passenger_data.get("date_of_birth"),
                gender=passenger_data.get("gender"),
                id_number=passenger_data.get("id_number"),
                single_room=passenger_data.get("single_room", False)
            )

        return num_single_rooms

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Cập nhật passengers thất bại", "error": str(e)}), 500