# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Heikki Toivonen

import os

from app import create_app, create_default_admin

app = create_app()

if __name__ == "__main__":
    # Create default admin user if no admin users exist
    with app.app_context():
        create_default_admin()

    # Only enable debug mode if FLASK_DEBUG environment variable is set to 'true'
    # In production, this should NOT be set
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode, host="127.0.0.1", port=8000)
