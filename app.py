import os
from app import create_app

def get_current_app():
    config_name = os.getenv('FLASK_CONFIG')
    app = create_app(config_name)
    return app
