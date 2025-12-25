import datetime
from decimal import Decimal
import uuid
from flask import current_app, jsonify, request
import cloudinary
from flask_jwt_extended import get_jwt_identity
from src.model.model_coupon import Coupons
from src.extension import db
from src.marshmallow.library_ma_coupon import (coupon_schema, coupons_schema)

#add favorite
def add_coupon_admin_service():
    try:
        code = request.form.get("code")
        description = request.form.get("description")
        discount_type = request.form.get("discount_type")
        discount_value = Decimal(request.form.get("discount_value"))
        min_order_amount = Decimal(request.form.get("min_order_amount"))
        max_discount_amount = Decimal(request.form.get("max_discount_amount"))
        usage_limit = int(request.form.get("usage_limit"))
        valid_from = request.form.get("valid_from")
        valid_to = request.form.get("valid_to")
        created_by = get_jwt_identity()
        coupon_image = request.files.get("coupon_image")

        required_fields = [code, discount_type, discount_value, min_order_amount, usage_limit, valid_from, valid_to]
        if not all(required_fields):
            return jsonify({"message":"Thiếu trường bắt buộc"}),400
        
        if Coupons.query.filter(Coupons.code.ilike(code)).first():
            return jsonify({"message":"Code coupon đã tồn tại"}),409
        
        if discount_type == "percentage":
            if discount_value <= 0 or discount_value > 100:
                return jsonify({"message": "Giảm giá % phải > 0 và ≤ 100"}), 400

        if discount_type == "fixed":
            if discount_value <= 0:
                return jsonify({"message": "Giảm giá cố định phải > 0"}), 400

        
        image_coupon_url = None
        image_coupon_public_id = None

        if coupon_image and coupon_image.filename:
            ext = coupon_image.filename.rsplit('.', 1)[1].lower() if '.' in coupon_image.filename else ''
            allowed = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
            if ext not in allowed:
                return jsonify({"message": "Định dạng ảnh không hợp lệ"}), 400
            
            try:
                unique_name = str(uuid.uuid4())
                upload_result = cloudinary.uploader.upload(
                    coupon_image,
                    folder="coupons",
                    public_id=unique_name,
                    format=ext,
                    transformation=[{'quality': "auto", 'fetch_format': "auto"}]
                )
                image_coupon_url = upload_result["secure_url"]
                image_coupon_public_id = upload_result["public_id"]
            except Exception as e:
                current_app.logger.error(f"Cloudinary upload failed: {str(e)}")
                return jsonify({"message": "Upload ảnh thất bại"}), 500
        new_coupon = Coupons(
            code = code,
            description = description,
            discount_type = discount_type,
            discount_value = discount_value,
            min_order_amount = min_order_amount,
            max_discount_amount = max_discount_amount,
            usage_limit = usage_limit,
            valid_from = valid_from,
            valid_to = valid_to,
            image_coupon_url = image_coupon_url,
            created_by=created_by,
            image_coupon_public_id = image_coupon_public_id
        )

        db.session.add(new_coupon)
        db.session.commit()
        return jsonify({"message": "Thêm mã giảm giá thành công"}), 201
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Lỗi thêm coupon: {str(e)}",
            exc_info=True
        )
        return jsonify({
            "message": "Thêm mã giảm giá thất bại",
            "error": str(e)
        }), 500
    
#get all coupon admin
def get_all_coupon_admin_service():
    try:
        coupons = Coupons.query.order_by(Coupons.created_at.desc()).all()
        if not coupons:
            return jsonify({"message":"Không có mã giảm giá nào trong hệ thống", "data":[]}),200
        return coupons_schema.dump(coupons),200
    except Exception as e:
        return jsonify({"message": f"Lỗi hệ thống khi lấy danh sách mã giảm giá: {str(e)}"}), 500  
