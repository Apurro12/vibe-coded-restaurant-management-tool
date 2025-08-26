from flask import Blueprint

movements_bp = Blueprint('movements', __name__, url_prefix='/movements')

from . import routes