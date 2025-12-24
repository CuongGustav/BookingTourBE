from datetime import datetime
import os
import uuid
import cloudinary
from flask import current_app, jsonify, request
from sqlalchemy import exists
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from src.model.model_booking import BookingStatusEnum, Bookings
from src.model.model_destination import Destinations
from src.model.model_tour import Tours
from src.model.model_tour_destination import Tour_Destinations
from src.model.model_tour_schedule import Tour_Schedules, ScheduleStatusEnum
from src.marshmallow.library_ma_tour import tour_schema,tourInfos_schema, tourInfo_schema
from src.marshmallow.library_ma_tour_schedules import tour_schedule_schema
from src.tour_images.services import get_tour_images_by_tour_id_service
from src.tour_schedules.services import get_tour_schedule_service
from src.tour_itineraries.services import get_tour_itineraries_by_tour_id_service
from src.destination.services import get_destination_by_tour_id_service
#generate tour code
def generate_tour_code():
    current_year = datetime.now().strftime("%Y")

    last_tour = Tours.query.filter(
        Tours.tour_code.like(f"TOUR-{current_year}%")
    ).order_by(Tours.created_at.desc()).first()
    if not last_tour or not last_tour.tour_code:
        new_code = f"TOUR-{current_year}A001"
    else:
        code_part = last_tour.tour_code.split('-')[-1]  
        year_part = code_part[:4]      
        group_letter = code_part[4]    
        number_part = code_part[5:]    
        if year_part != current_year:
            new_code = f"TOUR-{current_year}A001"
        else:
            num = int(number_part) + 1
            if num <= 999:
                new_code = f"TOUR-{current_year}{group_letter}{str(num).zfill(3)}"
            else:
                next_letter = chr(ord(group_letter) + 1) if group_letter != 'Z' else 'A'
                new_code = f"TOUR-{current_year}{next_letter}001"

    while Tours.query.filter_by(tour_code=new_code).first():
        new_code = f"TOUR-{current_year}{uuid.uuid4().hex[:6].upper()}"
    return new_code

#add tour
def create_tour_admin_service():
    try: 
        title = request.form.get("title")
        duration_days = request.form.get("duration_days")
        duration_nights = request.form.get("duration_nights")
        highlights = request.form.get("highlights")
        included_services = request.form.get("included_services")
        excluded_services = request.form.get("excluded_services")
        attractions = request.form.get("attractions")
        cuisine = request.form.get("cuisine")
        suitable_for = request.form.get("suitable_for")
        ideal_time = request.form.get("ideal_time")
        transportation = request.form.get("transportation")
        promotions = request.form.get("promotions")
        depart_destination = request.form.get("depart_destination")
        base_price = request.form.get("base_price")
        child_price = request.form.get("child_price")
        infant_price = request.form.get("infant_price")
        is_featured = request.form.get("is_featured")
        created_by = get_jwt_identity()
        main_image = request.files.get("main_image")

        required_fields = [title, duration_days, duration_nights, depart_destination,base_price]
        if not all(required_fields):
            return jsonify({"message":"Tiêu đề, số ngày, số đêm, điểm khởi hành, giá gốc là bắt buộc"}),400
        
        if Tours.query.filter(Tours.title.ilike(title)).first():
            return jsonify({"message":"Tiêu đề tour đã tồn tại"}),409
        
        is_featured = bool(int(is_featured)) if is_featured is not None else False
        
        tour_code = generate_tour_code()
        
        main_image_url = None
        main_image_public_id = None

        if main_image and main_image.filename:
            ext = main_image.filename.rsplit('.', 1)[1].lower() if '.' in main_image.filename else ''
            allowed = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
            if ext not in allowed:
                return jsonify({"message": "Định dạng ảnh không hợp lệ"}), 400

            try:
                unique_name = str(uuid.uuid4())
                upload_result = cloudinary.uploader.upload(
                    main_image,
                    folder="tours",
                    public_id=unique_name,
                    format=ext,
                    transformation=[{'quality': "auto", 'fetch_format': "auto"}]
                )
                main_image_url = upload_result["secure_url"]
                main_image_public_id = upload_result["public_id"]
            except Exception as e:
                current_app.logger.error(f"Cloudinary upload failed: {str(e)}")
                return jsonify({"message": "Upload ảnh thất bại"}), 500

        new_tour = Tours(
            tour_code = tour_code,
            title = title,
            duration_days = duration_days,
            duration_nights = duration_nights,
            highlights = highlights,
            included_services = included_services,
            excluded_services = excluded_services,
            attractions = attractions,
            cuisine = cuisine,
            suitable_for = suitable_for,
            ideal_time = ideal_time,
            transportation = transportation,
            promotions = promotions,
            depart_destination = depart_destination,
            base_price = base_price,
            child_price = child_price,
            infant_price = infant_price,
            main_image_url = main_image_url,
            main_image_public_id = main_image_public_id,
            is_featured = is_featured,
            created_by = created_by
        )
        db.session.add(new_tour)
        db.session.commit()
        tour_schema.dump(new_tour)
        return jsonify({"message": "Thêm tour thành công","tour_id": new_tour.tour_id,}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Lỗi thêm tour: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Thêm tour thất bại",
            "error": str(e)
        }), 500

#get all tour admin
def get_all_tour_admin_service():
    try:
        tours = Tours.query.order_by(Tours.created_at.desc()).all()
        if not tours:
            return jsonify({"message":"Không có tour nào trong hệ thống", "data":[]}),200
        return tourInfos_schema.dump(tours), 200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách điểm đến: {str(e)}"}), 500  
    
#get all tour
def get_all_tour_service():
    try:
        tours = (
            Tours.query
            .options(joinedload(Tours.schedules))
            .filter(Tours.is_active == True)
            .order_by(Tours.created_at.desc())
            .all()
        )
        result = []
        for tour in tours:
            tour_data = tourInfo_schema.dump(tour)  
            upcoming_schedules = (
                Tour_Schedules.query
                .filter(
                    Tour_Schedules.tour_id == tour.tour_id,
                    Tour_Schedules.departure_date >= datetime.now().date(),
                    Tour_Schedules.status == ScheduleStatusEnum.AVAILABLE.value
                )
                .order_by(Tour_Schedules.departure_date.asc())
                .limit(5)
                .all()
            )
            schedules_data = tour_schedule_schema.dump(upcoming_schedules)
            tour_data["upcoming_schedules"] = schedules_data
            result.append(tour_data)
        if not result:
            return jsonify({"message": "Không có tour nào trong hệ thống", "data": []}), 200
        return jsonify({"data": result, "length": len(result)}), 200

    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy danh sách tour: {str(e)}", exc_info=True)
        return jsonify({"message": f"Lỗi hệ thống: {str(e)}"}), 500 
    
#get 8 tour
def get_8_tour_service():
    try:
        tours = (
            Tours.query
            .options(joinedload(Tours.schedules))
            .filter(Tours.is_active == True)
            .order_by(Tours.created_at.desc())
            .limit(8)
            .all()
        )
        result = []
        for tour in tours:
            tour_data = tourInfo_schema.dump(tour)  
            upcoming_schedules = (
                Tour_Schedules.query
                .filter(
                    Tour_Schedules.tour_id == tour.tour_id,
                    Tour_Schedules.departure_date >= datetime.now().date(),
                    Tour_Schedules.status == ScheduleStatusEnum.AVAILABLE.value
                )
                .order_by(Tour_Schedules.departure_date.asc())
                .limit(2)
                .all()
            )
            schedules_data = tour_schedule_schema.dump(upcoming_schedules)
            tour_data["upcoming_schedules"] = schedules_data
            result.append(tour_data)
        if not result:
            return jsonify({"message": "Không có tour nào trong hệ thống", "data": []}), 200
        return jsonify({"data": result}), 200
    except Exception as e:
        current_app.logger.error(f"Lỗi khi lấy danh sách tour: {str(e)}", exc_info=True)
        return jsonify({"message": f"Lỗi hệ thống: {str(e)}"}), 500 
    
    
#get tour by filter
def filter_tours_service():
    try:
        data = request.get_json()
        budget = data.get("budget")

        departDestination = data.get("departDestination") 
        destination = data.get("destination")
        date = data.get("date")
        destination_info = None

        query = Tours.query.filter(Tours.is_active == True)

        # Filter by departDestination 
        if departDestination:
            query = query.filter(Tours.depart_destination.ilike(f"%{departDestination}%"))

        # Filter by destination 
        if destination:
            query = query.join(Tour_Destinations, Tours.tour_id == Tour_Destinations.tour_id)\
                .join(Destinations, Tour_Destinations.destination_id == Destinations.destination_id)\
                .filter(
                    Destinations.name.ilike(f"%{destination}%"),
                    Destinations.is_active == True
                )
            
            destination_obj = (
                Destinations.query
                .filter(
                    Destinations.name.ilike(f"%{destination}%"),
                    Destinations.is_active == True
                )
                .first()
            )
            if destination_obj:
                destination_info = {
                    "name": destination_obj.name,
                    "description": destination_obj.description
                }

        # Filter by budget - BẮT BUỘC nếu có
        if budget:
            if budget == "<5":
                query = query.filter(Tours.base_price < 5000000)
            elif budget == "5-10":
                query = query.filter(Tours.base_price.between(5000000, 10000000))
            elif budget == "10-20":
                query = query.filter(Tours.base_price.between(10000000, 20000000))
            elif budget == ">20":
                query = query.filter(Tours.base_price > 20000000)

        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d").date()
                query = query.filter(
                    exists().where(
                        (Tour_Schedules.tour_id == Tours.tour_id) &
                        (Tour_Schedules.departure_date == target_date) &
                        (Tour_Schedules.status == ScheduleStatusEnum.AVAILABLE.value)
                    )
                )
            except ValueError:
                return jsonify({
                    "message": "Ngày không hợp lệ, định dạng: YYYY-MM-DD"
                }), 400

        query = query.distinct()
        
        tours = query.order_by(Tours.created_at.desc()).all()

        result = []
        for tour in tours:
            tour_data = tourInfo_schema.dump(tour)

            if date:
                try:
                    target_date = datetime.strptime(date, "%Y-%m-%d").date()
                    upcoming_schedules = (
                        Tour_Schedules.query
                        .filter(
                            Tour_Schedules.tour_id == tour.tour_id,
                            Tour_Schedules.departure_date == target_date,
                            Tour_Schedules.status == ScheduleStatusEnum.AVAILABLE.value
                        )
                        .order_by(Tour_Schedules.departure_date.asc())
                        .all()
                    )
                except:
                    upcoming_schedules = []
            else:
                upcoming_schedules = (
                    Tour_Schedules.query
                    .filter(
                        Tour_Schedules.tour_id == tour.tour_id,
                        Tour_Schedules.departure_date >= datetime.now().date(),
                        Tour_Schedules.status == ScheduleStatusEnum.AVAILABLE.value
                    )
                    .order_by(Tour_Schedules.departure_date.asc())
                    .limit(5)
                    .all()
                )
            
            schedules_data = tour_schedule_schema.dump(upcoming_schedules)
            tour_data["upcoming_schedules"] = schedules_data

            result.append(tour_data)

        return jsonify({
            "tours": result,  
            "total": len(result),
            "destination": destination_info
        }), 200

    except Exception as e:
        current_app.logger.error(
            f"Lỗi khi filter tours: {str(e)}", 
            exc_info=True
        )
        return jsonify({
            "message": "Lỗi hệ thống khi lọc tour",
            "error": str(e)
        }), 500
    
#read tour
def get_tour_detail_service(tour_id):
    try:

        if not tour_id:
            return jsonify({"message": "Thiếu thông tin tour_id"}), 400

        tour = Tours.query.filter_by(tour_id=tour_id).first()
        if not tour:
            return jsonify({"message": "Không tìm thấy tour"}), 404
        if not tour.is_active:
            return jsonify({"message": "Tour đã bị ẩn hoặc ngừng hoạt động"}), 404
        
        tour_data = tour_schema.dump(tour)
        images = get_tour_images_by_tour_id_service(tour_id)
        schedules = get_tour_schedule_service(tour_id)
        itinararies = get_tour_itineraries_by_tour_id_service(tour_id)
        destinations = get_destination_by_tour_id_service(tour_id)
        
        tour_data["images"] = images
        tour_data["schedules"] = schedules
        tour_data["itineraries"] = itinararies
        tour_data["destinations"] = destinations

        return jsonify({"data": tour_data}), 200
    except Exception as e:
        print(f"[TourService] Lỗi ở hàm get_tour_detail_service: {str(e)}")
        return {
            "success": False,
            "message": "Lỗi hệ thống, vui lòng thử lại sau"
        }, 500
    
#read tour admin
def get_tour_detail_admin_service(tour_id):
    try:

        if not tour_id:
            return jsonify({"message": "Thiếu thông tin tour_id"}), 400

        tour = Tours.query.filter_by(tour_id=tour_id).first()
        if not tour:
            return jsonify({"message": "Không tìm thấy tour"}), 404
        
        tour_data = tour_schema.dump(tour)
        images = get_tour_images_by_tour_id_service(tour_id)
        schedules = get_tour_schedule_service(tour_id)
        itinararies = get_tour_itineraries_by_tour_id_service(tour_id)
        destinations = get_destination_by_tour_id_service(tour_id)
        
        tour_data["images"] = images
        tour_data["schedules"] = schedules
        tour_data["itineraries"] = itinararies
        tour_data["destinations"] = destinations

        return jsonify({"data": tour_data}), 200
    except Exception as e:
        print(f"[TourService] Lỗi ở hàm get_tour_detail_service: {str(e)}")
        return {
            "success": False,
            "message": "Lỗi hệ thống, vui lòng thử lại sau"
        }, 500

#delete tour (soft delete)
def delete_soft_tour_admin_service(tour_id):
    try:
        tour = Tours.query.filter_by(tour_id=tour_id).first()
        if not tour:
            return jsonify({"message": "Không tìm thấy tour"}), 404
        
        # check booking/payment is active yet
        active_bookings = Bookings.query.filter(
            Bookings.tour_id == tour_id,
            Bookings.status.in_([
                BookingStatusEnum.PENDING.value,
                BookingStatusEnum.CONFIRMED.value
            ])
        ).first()
        
        if active_bookings:
            return jsonify({
                "message": "Không thể xóa tour vì còn booking đang chờ xử lý hoặc đã xác nhận"
            }), 400
        
        # Soft delete: set is_active = False
        tour.is_active = False
        db.session.commit()
        
        return jsonify({
            "message": "Xóa mềm (ẩn) tour thành công",
            "note": "Lịch sử booking và thanh toán được giữ nguyên"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi xóa tour: {str(e)}", exc_info=True)
        return jsonify({
            "message": "Xóa tour thất bại",
            "error": str(e)
        }), 500
    
#update tour admin
def update_tour_admin_service(tour_id):
    try:
        tour = Tours.query.filter_by(tour_id=tour_id).first()
        if not tour:
            return jsonify({"message": "Không tìm thấy tour"}), 404
        
        title = request.form.get("title")
        duration_days = request.form.get("duration_days")
        duration_nights = request.form.get("duration_nights")
        highlights = request.form.get("highlights")
        included_services = request.form.get("included_services")
        excluded_services = request.form.get("excluded_services")
        attractions = request.form.get("attractions")
        cuisine = request.form.get("cuisine")
        suitable_for = request.form.get("suitable_for")
        ideal_time = request.form.get("ideal_time")
        transportation = request.form.get("transportation")
        promotions = request.form.get("promotions")
        depart_destination = request.form.get("depart_destination")
        base_price = request.form.get("base_price")
        child_price = request.form.get("child_price")
        infant_price = request.form.get("infant_price")
        is_featured_raw = request.form.get("is_featured")
        is_active_raw = request.form.get("is_active")
        main_image = request.files.get("main_image")

        required_fields = [title, duration_days, duration_nights, depart_destination, base_price]
        if not all(required_fields):
            return jsonify({"message": "Tiêu đề, số ngày, số đêm, điểm khởi hành, giá gốc là bắt buộc"}), 400
        
        if title != tour.title and Tours.query.filter(Tours.title.ilike(title), Tours.tour_id != tour_id).first():
            return jsonify({"message": "Tiêu đề tour đã tồn tại"}), 409
        
        try:
            duration_days = int(duration_days)
            duration_nights = int(duration_nights)
            base_price = float(base_price)
            child_price = float(child_price) if child_price and child_price != 'null' else None
            infant_price = float(infant_price) if infant_price and infant_price != 'null' else None
            
            if is_featured_raw is not None:
                is_featured = str(is_featured_raw).lower() in ['1', 'true']
            else:
                is_featured = tour.is_featured

            if is_active_raw is not None:
                is_active = str(is_active_raw).lower() in ['1', 'true']
            else:
                is_active = tour.is_active
        except ValueError:
            return jsonify({"message": "Dữ liệu số hoặc boolean không hợp lệ"}), 400
        
        main_image_url = tour.main_image_url
        main_image_public_id = tour.main_image_public_id

        if main_image and main_image.filename:
            ext = main_image.filename.rsplit('.', 1)[1].lower() if '.' in main_image.filename else ''
            allowed = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
            if ext not in allowed:
                return jsonify({"message": "Định dạng ảnh không hợp lệ"}), 400

            try:
                if main_image_public_id:
                    cloudinary.uploader.destroy(main_image_public_id)

                unique_name = str(uuid.uuid4())
                upload_result = cloudinary.uploader.upload(
                    main_image,
                    folder="tours",
                    public_id=unique_name,
                    format=ext,
                    transformation=[{'quality': "auto", 'fetch_format': "auto"}]
                )
                main_image_url = upload_result["secure_url"]
                main_image_public_id = upload_result["public_id"]
            except Exception as e:
                current_app.logger.error(f"Cloudinary upload failed: {str(e)}")
                return jsonify({"message": "Upload ảnh thất bại"}), 500
            
        tour.title = title
        tour.duration_days = duration_days
        tour.duration_nights = duration_nights
        tour.highlights = highlights 
        tour.included_services = included_services 
        tour.excluded_services = excluded_services 
        tour.attractions = attractions 
        tour.cuisine = cuisine 
        tour.suitable_for = suitable_for 
        tour.ideal_time = ideal_time
        tour.transportation = transportation 
        tour.promotions = promotions 
        tour.depart_destination = depart_destination
        tour.base_price = base_price
        tour.child_price = child_price
        tour.infant_price = infant_price
        tour.main_image_url = main_image_url
        tour.main_image_public_id = main_image_public_id
        tour.is_featured = is_featured
        tour.is_active = is_active

        db.session.commit()
        tour_schema.dump(tour)

        return jsonify({"message": "Cập nhật tour thành công", "tour_id": tour.tour_id}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi cập nhật tour: {str(e)}", exc_info=True)
        return jsonify({"message": "Cập nhật tour thất bại", "error": str(e)}), 500