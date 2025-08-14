# Admin API
from flask import Blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
def hello_admin():
    return "Hello, Admin!"
