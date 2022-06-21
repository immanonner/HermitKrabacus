from flask import Blueprint

bp = Blueprint('base_bp',
               __name__,
               static_folder='./static',
               template_folder='./templates',
               url_prefix='/base')
