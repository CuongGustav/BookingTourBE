import uuid
import cloudinary
from flask import current_app, jsonify, request
from src.extension import db
from src.model.model_tour import Tours
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
    
# update tour images by tour_id
def update_tour_images_admin_service(tour_id):

    if not tour_id:
            return jsonify({"message": "Thiếu tour_id"}), 400
    tour = Tours.query.get(tour_id)
    if not tour:
        return jsonify({"message": "Tour không tồn tại"}), 404
    try:
        image_ids_to_delete = request.form.getlist("image_ids")
        
        new_files = request.files.getlist("images")
        display_orders = request.form.getlist("display_orders")
        
        # Validate that at least one action is specified
        if not image_ids_to_delete and (not new_files or len(new_files) == 0 or new_files[0].filename == ''):
            return jsonify({"message": "Cần chỉ định ít nhất một hành động: xóa ảnh cũ hoặc thêm ảnh mới"}), 400
        
        # Validate new images and display orders match
        if new_files and new_files[0].filename != '':
            if len(new_files) != len(display_orders):
                return jsonify({"message": "Số lượng ảnh và display_order phải bằng nhau"}), 400
        
        deleted_images = []
        failed_deletes = []
        
        # Delete old images
        if image_ids_to_delete:
            for image_id in image_ids_to_delete:
                try:
                    image = Tour_Images.query.filter_by(
                        tour_image_id=image_id,
                        tour_id=tour_id
                    ).first()
                    
                    if not image:
                        failed_deletes.append({
                            "image_id": image_id,
                            "error": "Không tìm thấy ảnh"
                        })
                        continue
                    
                    # Delete from Cloudinary
                    if image.image_public_id:
                        try:
                            cloudinary.uploader.destroy(image.image_public_id)
                        except Exception as e:
                            current_app.logger.warning(
                                f"Failed to delete from Cloudinary: {image.image_public_id}, {str(e)}"
                            )
                    
                    # Delete from database
                    db.session.delete(image)
                    deleted_images.append(image_id)
                    
                except Exception as e:
                    current_app.logger.warning(f"Failed to delete image {image_id}: {str(e)}")
                    failed_deletes.append({
                        "image_id": image_id,
                        "error": str(e)
                    })
        
        # Upload new images
        created_images = []
        failed_uploads = []
        
        if new_files and new_files[0].filename != '':
            for idx, file in enumerate(new_files):
                if not file or file.filename == '':
                    failed_uploads.append({"index": idx, "error": "File rỗng"})
                    continue
                
                # Validate file extension
                ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                allowed = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
                if ext not in allowed:
                    failed_uploads.append({
                        "index": idx,
                        "error": f"Định dạng không cho phép: {ext}"
                    })
                    continue
                
                try:
                    # Upload to Cloudinary
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
                    
                    # Create new image record
                    new_image = Tour_Images(
                        tour_id=tour_id,
                        image_url=image_url,
                        image_public_id=image_public_id,
                        display_order=int(display_orders[idx])
                    )
                    db.session.add(new_image)
                    created_images.append(new_image)
                    
                except Exception as e:
                    current_app.logger.warning(
                        f"Cloudinary upload failed for image {idx}: {str(e)}"
                    )
                    failed_uploads.append({"index": idx, "error": str(e)})
        
        if failed_deletes or failed_uploads:
            db.session.rollback()
            return jsonify({
                "message": "Cập nhật ảnh tour không hoàn toàn thành công",
                "deleted": deleted_images,
                "delete_errors": failed_deletes,
                "upload_errors": failed_uploads
            }), 400
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({"message": "Cập nhật ảnh tour thành công"}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi cập nhật tour images: {str(e)}", exc_info=True)
        return jsonify({"message": "Cập nhật thất bại", "error": str(e)}), 500