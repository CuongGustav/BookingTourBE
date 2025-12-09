from flask import Flask
from flask_cors import CORS
from src.extension import db, ma, jwt, redis_blocklist
from src.auth.controller import auth
from src.account.controller import account
from src.destination.controller import destination
from src.tour.controller import tour
from src.tour_destinations.controller import tour_destinations

def create_app(config_file="config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    CORS(app, supports_credentials=True, origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000"
    ], allow_headers=["Content-Type", "Authorization"])

    # JWT cookie config
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = False  # False vì dev local (HTTP)
    app.config["JWT_COOKIE_SAMESITE"] = "Lax" # Hoặc "None" nếu cần cross-site
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
    app.config["JWT_REFRESH_COOKIE_PATH"] = "/auth/refresh"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False

    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(account, url_prefix="/account")  
    app.register_blueprint(destination, url_prefix="/destination")
    app.register_blueprint(tour, url_prefix="/tour")
    app.register_blueprint(tour_destinations, url_prefix="/tour_destinations")

    #JWT revoke check with Redis
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_data):
        jti = jwt_data["jti"]
        token_in_redis = redis_blocklist.get(jti)
        return token_in_redis is not None

    return app