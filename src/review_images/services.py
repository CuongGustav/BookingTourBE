import uuid
import cloudinary
import cloudinary.uploader
from flask import current_app
from src.extension import db
from src.model.model_review_image import ReviewImages


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
