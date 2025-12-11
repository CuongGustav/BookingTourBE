from datetime import datetime
import os
import uuid
import cloudinary
from flask import current_app, jsonify, request
from werkzeug.utils import secure_filename
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from src.model.model_tour import Tours
from src.marshmallow.library_ma_tour import tour_schema,tourInfos_schema

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

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DESTINATION_UPLOAD_FOLDER = os.path.join(
    BASE_DIR, "static", "tour"
)
DESTINATION_STATIC_URL = "/static/tour"
os.makedirs(DESTINATION_UPLOAD_FOLDER, exist_ok=True)

#add tour
def create_tour_admin_service():
    try: 
        title = request.form.get("title")
        slug = request.form.get("slug")
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
        main_image_local_path = None

        if main_image:
            ext = os.path.splitext(main_image.filename)[1]
            local_filename = f"{uuid.uuid4()}{ext}"
            # filesystem path
            main_image_local_path = os.path.join(
                DESTINATION_UPLOAD_FOLDER,
                secure_filename(local_filename)
            )
            main_image.save(main_image_local_path)
            # Cloudinary
            try:
                upload_result = cloudinary.uploader.upload(
                    main_image_local_path,
                    folder="tours"
                )
                main_image_url = upload_result.get("secure_url")
                main_image_public_id = upload_result.get("public_id")
            except Exception as e:
                current_app.logger.warning(
                    f"Cloudinary upload failed: {str(e)}"
                )
        new_tour = Tours(
            tour_code = tour_code,
            title = title,
            slug = slug,
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
            main_image_local_path = main_image_local_path,
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
        tours = Tours.query.filter(Tours.is_active == True).order_by(Tours.created_at.desc()).all()
        if not tours:
            return jsonify({"message":"Không có tour nào trong hệ thống", "data":[]}),200
        return tourInfos_schema.dump(tours), 200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách điểm đến: {str(e)}"}), 500  
    