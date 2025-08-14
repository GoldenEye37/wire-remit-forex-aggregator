# load environment variables from env file
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Flask
    DEBUG = os.environ.get("DEBUG")
    SECRET_KEY = os.environ.get("SECRET_KEY")
    CSRF_ENABLED = os.environ.get("CSRF_ENABLED")
    UUID_GENERATOR_FIELD_NAME = os.environ.get("UUID_GENERATOR_FIELD_NAME")

    # Database
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Exchange Rate API Clients
    EXCHANGE_RATE_API_CLIENT = os.environ.get("EXCHANGE_RATE_API_CLIENT")
    FIXER_IO_CLIENT = os.environ.get("FIXER_IO_CLIENT")
    POLYGON_CLIENT = os.environ.get("POLYGON_CLIENT")
