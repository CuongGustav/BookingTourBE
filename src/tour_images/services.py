import os
import uuid
import cloudinary
from werkzeug.utils import secure_filename
from flask import current_app, jsonify, request
from src.extension import db
from src.model.model_tour_image import Tour_Images


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
TOUR_UPLOAD_FOLDER = os.path.join(
    BASE_DIR, "static", "tour"
)
TOUR_STATIC_URL = "/static/tour"
os.makedirs(TOUR_UPLOAD_FOLDER, exist_ok=True)

def create_tour_images_admin_service():
    try:
        tour_id = request.form.get("tour_id")
        if not tour_id:
            return jsonify({"message": "Thiếu tour_id"}), 400
        
        files = request.files.getlist("images")
        display_orders = request.form.getlist("display_orders")
        if not files or len(files) == 0:
            return jsonify({"message": "Chưa chọn ảnh nào"}), 400
        if len(files) != len(display_orders):
            return jsonify({"message": "Số lượng ảnh và display_order phải bằng nhau"}), 400
        
        created_images = []
        failed_uploads = []
        for idx, file in enumerate(files):
            if file.filename == '':
                failed_uploads.append({"index": idx, "error": "File rỗng"})
                continue  
            ext = os.path.splitext(file.filename)[1]
            local_filename = f"{uuid.uuid4()}{ext}"
            image_local_path = os.path.join(
                TOUR_UPLOAD_FOLDER, 
                secure_filename(local_filename)
            )  
            file.save(image_local_path)
            image_url = None
            image_public_id = None
            try:
                upload_result = cloudinary.uploader.upload(
                    image_local_path,
                    folder="tours/gallery",
                    transformation={"quality": "auto", "fetch_format": "auto"}
                )
                image_url = upload_result.get("secure_url")
                image_public_id = upload_result.get("public_id")
                
                new_image = Tour_Images(
                    tour_id=tour_id,
                    image_url=image_url,
                    image_public_id=image_public_id,
                    image_local_path=image_local_path,
                    display_order=int(display_orders[idx])
                )
                db.session.add(new_image)
                created_images.append(new_image)
            except Exception as e:
                current_app.logger.warning(f"Cloudinary upload failed for image {idx}: {str(e)}")

        if failed_uploads:
            db.session.rollback()
            return jsonify({
                "message": "Một số ảnh upload thất bại",
                "errors": failed_uploads
            }), 400

        db.session.commit()
        return jsonify({"message": "Upload ảnh tour thành công",}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi upload tour images: {str(e)}", exc_info=True)
        return jsonify({"message": "Upload thất bại", "error": str(e)}), 500

                

