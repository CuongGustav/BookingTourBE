import uuid
import cloudinary
from flask import current_app, jsonify, request
from src.extension import db
from src.model.model_tour_image import Tour_Images
from src.marshmallow.library_ma_tour_images import tour_images_read_schema

#create tour image
def create_tour_images_admin_service():
    try:
        tour_id = request.form.get("tour_id")
        if not tour_id:
            return jsonify({"message": "Thiếu tour_id"}), 400
        
        files = request.files.getlist("images")
        display_orders = request.form.getlist("display_orders")
        if not files or len(files) == 0 or files[0].filename == '':
            return jsonify({"message": "Chưa chọn ảnh nào"}), 400
        if len(files) != len(display_orders):
            return jsonify({"message": "Số lượng ảnh và display_order phải bằng nhau"}), 400
        
        created_images = []
        failed_uploads = []
        for idx, file in enumerate(files):
            if not file or file.filename == '':
                failed_uploads.append({"index": idx, "error": "File rỗng"})
                continue  

            ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            allowed = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
            if ext not in allowed:
                failed_uploads.append({"index": idx, "error": f"Định dạng không cho phép: {ext}"})
                continue

            try:
                unique_name = str(uuid.uuid4())
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder="tours/gallery",
                    public_id=unique_name,
                    format=ext,
                    transformation=[{'quality': "auto", 'fetch_format': "auto"}]
                )
                image_url = upload_result["secure_url"]
                image_public_id = upload_result["public_id"]
                
                new_image = Tour_Images(
                    tour_id=tour_id,
                    image_url=image_url,
                    image_public_id=image_public_id,
                    display_order=int(display_orders[idx])
                )
                db.session.add(new_image)
                created_images.append(new_image)
            except Exception as e:
                current_app.logger.warning(f"Cloudinary upload failed for image {idx}: {str(e)}")
                failed_uploads.append({"index": idx, "error": str(e)})

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

#get tour image by tour_id
def get_tour_images_by_tour_id_service (tour_id: str):
    try:
        images = (
            Tour_Images.query
            .filter_by(tour_id=tour_id)
            .order_by(Tour_Images.display_order.asc())
            .all()
        ) 
        if not images:
            return []

        result = tour_images_read_schema.dump(images)
        return result
    except Exception as e:
        print(f"[TourImagesService] Lỗi ở hàm get_tour_image_by_tour_id_service {tour_id}: {str(e)}")
        db.session.rollback()
        return []

