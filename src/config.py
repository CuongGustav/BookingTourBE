import os
import cloudinary
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = os.getenv("DB_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = os.getenv("FLASK_JWT_SECRET_KEY")
REDIS_URL = os.getenv("REDIS_URL")

# Add these JWT cookie configurations
JWT_TOKEN_LOCATION = ["cookies"]
JWT_COOKIE_SECURE = False  # Set to True in production with HTTPS
JWT_COOKIE_CSRF_PROTECT = False  # Set to True in production
JWT_ACCESS_COOKIE_PATH = "/"
JWT_REFRESH_COOKIE_PATH = "/"
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_DOMAIN = None  # Or set to "localhost" for local development

#google oauth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID") 
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET") 
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

#cloudinary
CLOUDINARY_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
    cloud_name = CLOUDINARY_NAME,
    api_key = CLOUDINARY_API_KEY,
    api_secret = CLOUDINARY_API_SECRET,
    secure = True
)