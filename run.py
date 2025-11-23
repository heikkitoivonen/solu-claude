import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Only enable debug mode if FLASK_DEBUG environment variable is set to 'true'
    # In production, this should NOT be set
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="127.0.0.1", port=8000)
