from flask import Flask
from flask_cors import CORS
from src.extension import db, ma, jwt, redis_blocklist
from src.auth.controller import auth

def create_app(config_file="config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000"
    ], allow_headers=["Content-Type", "Authorization"])

    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth, url_prefix="/auth")

    #JWT revoke check with Redis
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_data):
        jti = jwt_data["jti"]
        token_in_redis = redis_blocklist.get(jti)
        return token_in_redis is not None

    return app