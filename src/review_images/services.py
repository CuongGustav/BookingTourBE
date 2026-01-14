import uuid
import cloudinary
import cloudinary.uploader
from flask import current_app
from src.extension import db
from src.model.model_review_image import ReviewImages

#create review images
def create_review_image(review_id, files):
    uploaded_images = []
    failed_uploads = []

    for idx, file in enumerate(files):
        if not file or file.filename == '':
            failed_uploads.append({"index": idx, "error": "File rỗng"})
            continue

        file.seek(0)

        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        allowed = {'jpg', 'jpeg', 'png', 'webp', 'gif'}
        if ext not in allowed:
            failed_uploads.append({"index": idx, "error": f"Định dạng không cho phép: {ext}"})
            continue

        try:
            upload_result = cloudinary.uploader.upload(
                file,
                folder="reviews",
                public_id=str(uuid.uuid4()),
                transformation=[{'quality': "auto", 'fetch_format': "auto"}]
            )

            new_image = ReviewImages(
                review_id=review_id,
                image_url=upload_result["secure_url"],
                image_public_id=upload_result["public_id"]
            )
            db.session.add(new_image)

            uploaded_images.append({
                "image_id": new_image.image_id,
                "image_url": upload_result["secure_url"]
            })

        except Exception as e:
            current_app.logger.exception("Upload ảnh thất bại")
            failed_uploads.append({"index": idx, "error": str(e)})

    if failed_uploads:
        raise Exception(f"Một số ảnh upload thất bại: {failed_uploads}")

    return uploaded_images

#delete review image
def delete_review_images(review_id):
    deleted_images = []
    failed_deletes = []

    images = ReviewImages.query.filter_by(review_id=review_id).all()
    
    for image in images:
        try:
            # Xóa từ Cloudinary
            cloudinary.uploader.destroy(image.image_public_id)
            # Xóa từ database
            db.session.delete(image)
            deleted_images.append(image.image_id)
        except Exception as e:
            current_app.logger.error(f"Lỗi khi xóa image {image.image_id}: {str(e)}")
            failed_deletes.append({"image_id": image.image_id, "error": str(e)})

    if failed_deletes:
        raise Exception(f"Một số ảnh xóa thất bại: {failed_deletes}")

    return deleted_images

#delete image for update
def delete_review_images_by_ids(review_id: str, image_ids: list):
    deleted_ids = []
    failed = []

    images = ReviewImages.query.filter(
        ReviewImages.review_id == review_id,
        ReviewImages.image_id.in_(image_ids)
    ).all()

    for image in images:
        try:
            cloudinary.uploader.destroy(image.image_public_id)
            db.session.delete(image)
            deleted_ids.append(image.image_id)
        except Exception as e:
            current_app.logger.error(f"Lỗi xóa ảnh {image.image_id}: {str(e)}")
            failed.append({"image_id": image.image_id, "error": str(e)})

    if failed:
        raise Exception(f"Một số ảnh xóa thất bại: {failed}")

    return deleted_ids