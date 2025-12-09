import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app, jsonify, request
from werkzeug.utils import secure_filename
from src.extension import db
from src.model.model_destination import Destinations
from src.marshmallow.library_ma_destination import destination_schema, destinations_schema, destinationRegions_schema, destinationCreateTour_schema
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

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DESTINATION_UPLOAD_FOLDER = os.path.join(
    BASE_DIR, "static", "destination"
)
DESTINATION_STATIC_URL = "/static/destination"
os.makedirs(DESTINATION_UPLOAD_FOLDER, exist_ok=True)

#add destination
@require_role("qcadmin")
def add_destination_service():
    try:
        name = request.form.get("name")
        country = request.form.get("country")
        region = request.form.get("region")
        description = request.form.get("description")
        image = request.files.get("image")

        if not name or not country:
            return jsonify({"message": "Tên và quốc gia là bắt buộc"}), 400

        if Destinations.query.filter(
            Destinations.name.ilike(name)
        ).first():
            return jsonify({"message": "Tên điểm đến đã tồn tại."}), 409

        image_url = None
        image_public_id = None
        image_local_path = None

        if image:
            ext = os.path.splitext(image.filename)[1]
            local_filename = f"{uuid.uuid4()}{ext}"
            # filesystem path
            image_local_path = os.path.join(
                DESTINATION_UPLOAD_FOLDER,
                secure_filename(local_filename)
            )
            image.save(image_local_path)
            # Cloudinary
            try:
                upload_result = cloudinary.uploader.upload(
                    image_local_path,
                    folder="destinations"
                )
                image_url = upload_result.get("secure_url")
                image_public_id = upload_result.get("public_id")
            except Exception as e:
                current_app.logger.warning(
                    f"Cloudinary upload failed: {str(e)}"
                )

        new_destination = Destinations(
            name=name,
            country=country,
            region=region,
            description=description,
            image_url=image_url,
            image_public_id=image_public_id,
            image_local_path=image_local_path,
            is_active=True
        )
        db.session.add(new_destination)
        db.session.commit()
        destination_schema.dump(new_destination)
        return jsonify({"message": "Thêm điểm đến thành công",}), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"lỗi thêm destination: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Thêm điểm đến thất bại",
            "error": str(e)
        }), 500
    
#get all destination admin
@require_role('qcadmin')
def get_all_destination_admin_service ():
    try:
        destinations = Destinations.query.order_by(Destinations.created_at.desc()).all()
        if not destinations:
            return jsonify({"message":"Không có địa điểm nào trong hệ thống", "data":[]}),200
        return destinations_schema.dump(destinations),200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách điểm đến: {str(e)}"}), 500  
    
#get destination by uuid admin
@require_role('qcadmin')
def get_destination_by_uuid_admin_service (destination_id):
    if not destination_id:
        return jsonify({"message": "Thiếu thông tin destination_id"}), 400
    
    destination = Destinations.query.filter_by(destination_id=destination_id).first()
    if not destination:
        return jsonify({"message": "Không tìm thấy điểm đến"}), 404
    
    return destination_schema.dump(destination), 200
    
#update destination by admin
@require_role("qcadmin")
def update_destination_admin_service(destination_id):
    try:
        destination = Destinations.query.filter_by(
            destination_id=destination_id
        ).first()

        if not destination:
            return jsonify({"message": "Không tìm thấy điểm đến"}), 404

        name = request.form.get("name")
        country = request.form.get("country")
        region = request.form.get("region")
        description = request.form.get("description")
        image = request.files.get("image")
        is_active = request.form.get("is_active")
        delete_image = request.form.get("delete_image")


        if name:
            destination.name = name
        if country:
            destination.country = country
        if region is not None:
            destination.region = region
        if description is not None:
            destination.description = description
        if is_active is not None:
            new_is_active = int(is_active) == 1
            if destination.is_active != new_is_active:
                destination.is_active = new_is_active

        # delete image only
        if delete_image == "true":
            # delete cloudinary image
            if destination.image_public_id:
                try:
                    cloudinary.uploader.destroy(
                        destination.image_public_id
                    )
                except Exception as e:
                    current_app.logger.warning(
                        f"Delete Cloudinary image failed: {str(e)}"
                    )
            # delete local image
            if destination.image_local_path and os.path.exists(
                destination.image_local_path
            ):
                try:
                    os.remove(destination.image_local_path)
                except Exception as e:
                    current_app.logger.warning(
                        f"Delete local image failed: {str(e)}"
                    )
            destination.image_url = None
            destination.image_public_id = None
            destination.image_local_path = None

        #upload new image
        if image:
            # remove image Cloudinary old
            if destination.image_public_id:
                try:
                    cloudinary.uploader.destroy(
                        destination.image_public_id
                    )
                except Exception as e:
                    current_app.logger.warning(
                        f"Delete old Cloudinary image failed: {str(e)}"
                    )

            # remove image local
            if destination.image_local_path and os.path.exists(
                destination.image_local_path
            ):
                try:
                    os.remove(destination.image_local_path)
                except Exception as e:
                    current_app.logger.warning(
                        f"Delete old local image failed: {str(e)}"
                    )

            # save image
            ext = os.path.splitext(image.filename)[1]
            local_filename = f"{uuid.uuid4()}{ext}"

            new_local_path = os.path.join(
                DESTINATION_UPLOAD_FOLDER,
                secure_filename(local_filename)
            )

            image.save(new_local_path)

            #Upload Cloudinary
            image_url = None
            image_public_id = None

            try:
                upload_result = cloudinary.uploader.upload(
                    new_local_path,
                    folder="destinations"
                )
                image_url = upload_result.get("secure_url")
                image_public_id = upload_result.get("public_id")
            except Exception as e:
                current_app.logger.warning(
                    f"Cloudinary upload failed: {str(e)}"
                )

            destination.image_local_path = new_local_path
            destination.image_url = image_url
            destination.image_public_id = image_public_id

        db.session.commit()

        return jsonify({
            "message": "Cập nhật điểm đến thành công",
            "data": destination_schema.dump(destination)
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"LỖI UPDATE DESTINATION: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Failed to update destination",
            "error": str(e)
        }), 500

#delete destination by admin
@require_role("qcadmin")
def delete_destination_admin_service(destination_id):
    try:
        destination = Destinations.query.filter_by(
            destination_id=destination_id
        ).first()

        if not destination:
            return jsonify({
                "message": "Không tìm thấy điểm đến"
            }), 404

        if destination.tours and len(destination.tours) > 0:
            return jsonify({
                "message": "Không thể xoá điểm đến vì đang có tour sử dụng",
                "total_tours": len(destination.tours)
            }), 400

        if destination.image_public_id:
            try:
                cloudinary.uploader.destroy(
                    destination.image_public_id
                )
            except Exception as e:
                current_app.logger.warning(
                    f"Delete Cloudinary image failed: {str(e)}"
                )

        if destination.image_local_path and os.path.exists(
            destination.image_local_path
        ):
            try:
                os.remove(destination.image_local_path)
            except Exception as e:
                current_app.logger.warning(
                    f"Delete local image failed: {str(e)}"
                )

        db.session.delete(destination)
        db.session.commit()

        return jsonify({
            "message": "Xoá điểm đến thành công"
        }), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"LỖI XOÁ DESTINATION: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Failed to delete destination",
            "error": str(e)
        }), 500

#get all destination by region
def get_all_destination_by_region_service():
    try:
        region = request.args.get("region")
        if not region:
            return jsonify({"message": "Thiếu tham số"}),400
        
        destinations = Destinations.query.filter(
                            Destinations.region.ilike(f"%{region.strip()}%"),
                            Destinations.is_active==True).order_by(Destinations.name
                        ).all()
        
        if not destinations:
            return jsonify({"message": "Không tìm thấy điểm đến nào cho khu vực này"}), 200
        
        result = destinationRegions_schema.dump(destinations)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"message": f"Có lỗi xảy ra, vui lòng thử lại sau: {str(e)}"}), 500

#get all destination create tour admin
def get_all_destination_create_tour_admin_service ():
    try:
        destinations = Destinations.query.order_by(Destinations.created_at.desc()).all()
        if not destinations:
            return jsonify({"message":"Không có địa điểm nào trong hệ thống", "data":[]}),200
        return destinationCreateTour_schema.dump(destinations),200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách điểm đến: {str(e)}"}), 500  