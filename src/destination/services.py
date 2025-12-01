import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app, jsonify, request
from werkzeug.utils import secure_filename
from src.extension import db
from src.model.model_destination import Destinations
from src.marshmallow.library_ma_destination import destination_schema
from src.common.decorators import require_role

#check cloudinary usege
def get_cloudinary_usage_service():
    try:
        usage = cloudinary.api.usage()

        return jsonify({
            "plan": usage.get("plan", "unknown"),
            "last_updated": usage.get("last_updated", ""),
            "storage_bytes": usage.get("storage_bytes", {}).get("usage", 0),
            "bandwidth_bytes": usage.get("bandwidth_bytes", {}).get("usage", 0),
            "objects_count": usage.get("objects_count", {}).get("usage", 0),
            "message": "Cloudinary usage fetched successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "message": "Failed to fetch Cloudinary usage",
            "error": str(e)
        }), 500
    
DESTINATION_STATIC_FOLDER = "D:/workspace/BookingTourBE/static/destination"
if not os.path.exists(DESTINATION_STATIC_FOLDER):
    os.makedirs(DESTINATION_STATIC_FOLDER)

#add destination 
@require_role('qcadmin')
def add_destination_service():
    try:
        # Lấy dữ liệu từ request
        name = request.form.get("name")
        country = request.form.get("country")
        region = request.form.get("region")
        description = request.form.get("description")
        image = request.files.get("image")

        if not name or not country:
            return jsonify({"message": "Name and country are required"}), 400

        image_url = None
        image_public_id = None
        local_backup_path = None

        if image:
            # 1️⃣ Backup cục bộ
            ext = os.path.splitext(image.filename)[1]
            local_filename = f"{uuid.uuid4()}{ext}"
            local_backup_path = os.path.join(DESTINATION_STATIC_FOLDER, secure_filename(local_filename))
            image.save(local_backup_path)

            # 2️⃣ Upload lên Cloudinary
            try:
    
                result = cloudinary.uploader.upload(local_backup_path, folder="destinations")
                image_url = result.get("secure_url")
                image_public_id = result.get("public_id")
            except Exception as e:
                # Nếu Cloudinary fail, vẫn có backup local
                image_url = None
                image_public_id = None
                current_app.logger.warning(f"Cloudinary upload failed: {str(e)}")

        # Tạo object destination
        new_destination = Destinations(
            name=name,
            country=country,
            region=region,
            description=description,
            image_url=image_url,
            image_public_id=image_public_id,
            is_active=True
        )

        db.session.add(new_destination)
        db.session.commit()

        response_data = destination_schema.dump(new_destination)
        # Nếu Cloudinary fail, dùng backup local path làm image_url tạm
        if not image_url and local_backup_path:
            response_data["image_url"] = f"/static/destination/{os.path.basename(local_backup_path)}"

        return jsonify({"message": "Thêm điểm đến thành công"}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"LỖI THÊM DESTINATION: {str(e)}", exc_info=True)  # ← THÊM DÒNG NÀY
        return jsonify({
            "message": "Failed to add destination",
            "error": str(e)                     # ← Trả luôn lỗi thật về frontend
        }), 500