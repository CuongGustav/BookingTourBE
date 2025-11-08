import os
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