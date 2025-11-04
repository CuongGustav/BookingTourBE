import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = os.getenv("DB_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False
JWT_SECRET_KEY = os.getenv("FLASK_JWT_SECRET_KEY")
REDIS_URL = os.getenv("REDIS_URL")