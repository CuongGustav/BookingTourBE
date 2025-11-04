from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager
import redis
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()

redis_blocklist = redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)