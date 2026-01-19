import os
from src import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    flask_env = os.environ.get("FLASK_ENV", "production")
    is_production = flask_env == "production"
    debug_mode = not is_production
    
    print(f"Starting app on port {port}, debug={debug_mode}, env={flask_env}")
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)