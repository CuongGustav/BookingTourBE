import os
from flask import Flask
from flask_cors import CORS
from src.extension import db, ma, jwt, redis_blocklist
from src.auth.controller import auth
from src.account.controller import account
from src.destination.controller import destination
from src.tour.controller import tour
from src.tour_destinations.controller import tour_destinations
from src.tour_itineraries.controller import tour_itineraries
from src.tour_schedules.controller import tour_schedules
from src.tour_images.controller import tour_images
from src.favorites.controller import favorites
from src.coupon.controller import coupon
from src.booking.controller import booking
from src.booking_passengers.controller import booking_passengers
from src.payment.controller import payment
from src.update_status_completed_booking import init_scheduler
from src.reviews.controller import reviews
from src.statics.controller import statics

def create_app(config_file="config.py"):
    app = Flask(__name__)
    app.config.from_pyfile(config_file)

    fe_url = app.config.get('FE_URL')
    origins = [fe_url] if fe_url else ["http://localhost:3000", "http://127.0.0.1:3000"]  

    CORS(app, supports_credentials=True, origins=origins,
         allow_headers=["Content-Type", "Authorization"])

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
        if os.getenv("FLASK_ENV") != "production":
            db.create_all()
        init_scheduler(app)

    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(account, url_prefix="/account")  
    app.register_blueprint(destination, url_prefix="/destination")
    app.register_blueprint(tour, url_prefix="/tour")
    app.register_blueprint(tour_destinations, url_prefix="/tour_destinations")
    app.register_blueprint(tour_itineraries, url_prefix="/tour_itineraries")
    app.register_blueprint(tour_schedules, url_prefix="/tour_schedules")
    app.register_blueprint(tour_images, url_prefix="/tour_images")
    app.register_blueprint(favorites, url_prefix="/favorites")
    app.register_blueprint(coupon, url_prefix="/coupon")
    app.register_blueprint(booking, url_prefix="/booking")
    app.register_blueprint(booking_passengers, url_prefix="/booking-passengers")
    app.register_blueprint(payment, url_prefix="/payment")
    app.register_blueprint(reviews, url_prefix="/reviews")
    app.register_blueprint(statics, url_prefix="/statics")


    #JWT revoke check with Redis
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_data):
        jti = jwt_data["jti"]
        if not redis_blocklist:
            return False
        token_in_redis = redis_blocklist.get(jti)
        return token_in_redis is not None

    return app