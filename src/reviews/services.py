from decimal import Decimal
from flask import current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity
from src.extension import db
from src.model.model_booking import Bookings, BookingStatusEnum
from src.model.model_tour import Tours
from src.model.model_review import Reviews
from src.review_images.services import create_review_image, delete_review_images
from src.marshmallow.library_ma_review import reviews_schema

#create review user
def create_review_service():
    try:
        account_id = get_jwt_identity()
        data = request.form
        booking_id = data.get("booking_id")
        tour_id = data.get("tour_id")
        rating = data.get("rating")
        comment = data.get("comment")

        if not all([booking_id, tour_id, rating, comment]):
            return jsonify({"message": "Thiếu thông tin: booking_id, tour_id, rating, comment"}), 400
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return jsonify({"message": "Đánh giá phải từ 1 đến 5"}), 400
        except ValueError:
            return jsonify({"message": "Đánh giá không hợp lệ"}), 400
        
        booking = Bookings.query.get(booking_id)
        if not booking:
            return jsonify({"message": "Không tìm thấy booking"}), 404
        
        tour = Tours.query.get(tour_id)
        if not tour:
            return jsonify({"message": "Không tìm thấy tour"}), 404
        
        if booking.account_id != account_id:
            return jsonify({"message": "Không có quyền đánh giá booking này"}), 403
        
        if booking.status != BookingStatusEnum.COMPLETED:
            return jsonify({"message": "Booking chưa hoàn thành để đánh giá"}), 400
        
        existing_review = Reviews.query.filter_by(
            booking_id=booking_id,
            account_id=account_id
        ).first()
        if existing_review:
            return jsonify({"message": "Booking này đã được đánh giá"}), 400
        
        new_review = Reviews(
            tour_id=tour_id,
            booking_id=booking_id,
            account_id=account_id,
            rating=rating,
            comment=comment,
        )
        db.session.add(new_review)
        db.session.flush()

        files = request.files.getlist("images")
        uploaded_images = []
        
        if files and len(files) > 0 and files[0].filename != '':
            try:
                uploaded_images = create_review_image(new_review.review_id, files)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"upload ảnh thất bại: {str(e)}")
                return jsonify({
                    "message": "upload ảnh thất bại",
                    "error": str(e)
                }), 400
        
        total_reviews = tour.total_reviews + 1
        new_average = (
            tour.rating_average * Decimal(tour.total_reviews) + Decimal(rating)
        ) / Decimal(total_reviews)
        tour.total_reviews = total_reviews
        tour.rating_average = new_average.quantize(Decimal("0.00"))
        
        db.session.commit()

        response_data = {
            "message": "Đánh giá thành công",
            "review_id": new_review.review_id
        }
        
        if uploaded_images:
            response_data["uploaded_images"] = uploaded_images
            response_data["total_images"] = len(uploaded_images)

        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo đánh giá: {str(e)}")
        return jsonify({"message": "Lỗi khi tạo đánh giá", "error": str(e)}), 500
    
#get all review user
def get_all_review_user_service():
    try:
        account_id = get_jwt_identity()
        if not account_id:
            return jsonify({"message": "Không tìm thấy account_id từ token"}), 401
        
        reviews = Reviews.query.filter_by(account_id=account_id).all()
        reviews_data = reviews_schema.dump(reviews)

        return jsonify({"reviews": reviews_data}), 200

    except Exception as e:
        current_app.logger.error(f"Lỗi lấy reviews: {str(e)}", exc_info=True)
        return jsonify({"message": "Lấy reviews thất bại", "error": str(e)}), 500

# delete review user
def delete_review_service(review_id):
    try:
        account_id = get_jwt_identity()

        if not review_id:
            return jsonify({"message": "Thiếu thông tin: review_id"}), 400
        
        review = Reviews.query.get(review_id)
        if not review:
            return jsonify({"message": "Không tìm thấy review"}), 404
        
        if review.account_id != account_id:
            return jsonify({"message": "Không có quyền xóa review này"}), 403
        
        tour = Tours.query.get(review.tour_id)
        if not tour:
            return jsonify({"message": "Không tìm thấy tour liên quan"}), 404
        
        deleted_images = delete_review_images(review.review_id)
        
        removed_rating = review.rating
        db.session.delete(review)
        
        if tour.total_reviews > 0:
            old_total = tour.total_reviews
            new_total = old_total - 1
            if new_total > 0:
                new_average = (
                    (tour.rating_average * Decimal(old_total) - Decimal(removed_rating)) / Decimal(new_total)
                ).quantize(Decimal("0.00"))
            else:
                new_average = Decimal("0.00")
            tour.total_reviews = new_total
            tour.rating_average = new_average
        
        db.session.commit()

        response_data = {
            "message": "Xóa review thành công",
            "review_id": review_id
        }
        
        if deleted_images:
            response_data["deleted_images"] = deleted_images
            response_data["total_deleted_images"] = len(deleted_images)

        return jsonify(response_data), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi xóa review: {str(e)}")
        return jsonify({"message": "Lỗi khi xóa review", "error": str(e)}), 500