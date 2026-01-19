import cloudinary
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
import redis
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()

REDIS_URL = os.getenv("REDIS_PUBLIC_URL")

redis_blocklist = None

if REDIS_URL:
    try:
        redis_blocklist = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        redis_blocklist.ping()
        print("Redis connected successfully")
    except Exception as e:
        print("Redis connection failed:", e)
        redis_blocklist = None
else:
    print("⚠ Redis URL not found, JWT revoke will be disabled")
