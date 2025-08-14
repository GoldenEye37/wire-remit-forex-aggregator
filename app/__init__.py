# Flask app initialization
import os

from flask import Flask
from loguru import logger

from config import Config
from app.extensions import db

def create_app():
    app = Flask(__name__)
    
    logger.info(f"MY IP: {os.environ.get('DB_HOST')}")
    app.config.from_object(Config)

    db.init_app(app)

    # blueprints

    return app