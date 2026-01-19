import os
from src import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    
    is_production = "production"
    debug_mode = not is_production
    
    app.run(host="0.0.0.0", port=port, debug=debug_mode)