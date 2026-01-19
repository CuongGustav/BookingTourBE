import os
import cloudinary
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("CHECKING ENVIRONMENT VARIABLES:")
db_url = os.getenv("DB_URL")
database_url = os.getenv("DATABASE_URL")
mysql_url = os.getenv("MYSQL_URL")
redis_url = os.getenv("REDIS_PUBLIC_URL") or os.getenv("REDIS_URL")
fe_url = os.getenv("FE_URL")

print(f"DB_URL: {'Found' if db_url else 'Not found'}")
print(f"DATABASE_URL: {'Found' if database_url else 'Not found'}")
print(f"MYSQL_URL: {'Found' if mysql_url else 'Not found'}")
print(f"FE_URL: {'Found' if fe_url else 'Not found'}")
print(f"REDIS_PUBLIC_URL/REDIS_URL: {'Found' if redis_url else 'Not found'}")
print("=" * 50)

DATABASE_URL = (
    os.getenv("DB_URL") or 
    os.getenv("DATABASE_URL") or 
    os.getenv("MYSQL_URL")
)

if not DATABASE_URL:
    raise RuntimeError("Thiếu biến môi trường Database URL (đã thử DB_URL, DATABASE_URL, MYSQL_URL)")
SQLALCHEMY_DATABASE_URI = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = os.getenv("FLASK_JWT_SECRET_KEY")

REDIS_PUBLIC_URL = (
    os.getenv("REDIS_PUBLIC_URL") or
    os.getenv("REDIS_URL")
)

# Add these JWT cookie configurations
JWT_TOKEN_LOCATION = ["cookies"]
JWT_COOKIE_SECURE = True  # Set to True in production with HTTPS
JWT_COOKIE_CSRF_PROTECT = False  # Set to True in production
JWT_ACCESS_COOKIE_PATH = "/"
JWT_REFRESH_COOKIE_PATH = "/"
JWT_COOKIE_SAMESITE = None
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

#FE URL
FE_URL = os.getenv("FE_URL")