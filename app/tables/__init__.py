from flask import Blueprint

tables_bp = Blueprint('tables', __name__, url_prefix='/tables')

from . import routes