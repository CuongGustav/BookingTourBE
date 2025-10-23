from flask import Flask
from flask_cors import CORS
from .extension import db, ma

def create_app(config_file="config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    CORS(app)

    db.init_app(app)
    ma.init_app(app)

    return app