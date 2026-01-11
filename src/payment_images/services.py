import uuid
import cloudinary
from flask import current_app
from src.extension import db
from src.model.model_payment_image import PaymentImages


def create_payment_image(payment_id, files):
    uploaded_images = []
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
                folder="payments",
                public_id=unique_name,
                format=ext,
                transformation=[{'quality': "auto", 'fetch_format': "auto"}]
            )
            image_url = upload_result["secure_url"]
            image_public_id = upload_result["public_id"]
            
            new_image = PaymentImages(
                payment_id=payment_id,
                image_url=image_url,
                image_public_id=image_public_id
            )
            db.session.add(new_image)
            uploaded_images.append({
                "image_id": new_image.image_id,
                "image_url": image_url
            })
        except Exception as e:
            current_app.logger.warning(f"Cloudinary upload failed for image {idx}: {str(e)}")
            failed_uploads.append({"index": idx, "error": str(e)})

    if failed_uploads:
        raise Exception(f"Một số ảnh upload thất bại: {failed_uploads}")
    
    return uploaded_images