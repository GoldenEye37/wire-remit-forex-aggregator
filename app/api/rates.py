# Rates API
from flask import Blueprint

rates_bp = Blueprint('rates', __name__, url_prefix='/rates')

@rates_bp.route('/', methods=['GET'])
def get_rates():
    return "Here are the exchange rates"
    
