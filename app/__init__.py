# Flask app initialization
import os

from flask import Flask
from loguru import logger

from config import Config
from .extensions import db
from .api import auth, rates, admin

def create_app():
    app = Flask(__name__)

    logger.info(f"MY IP: {os.environ.get('DB_HOST')}")

    app.config.from_object(Config)
    db.init_app(app)

    # blueprints
    from .api.auth import auth_bp
    from .api.rates import rates_bp
    from .api.admin import admin_bp

    from flask import Blueprint
    
    api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1.0')
    
    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(rates_bp)
    api_v1.register_blueprint(admin_bp)

    app.register_blueprint(api_v1)
    return app