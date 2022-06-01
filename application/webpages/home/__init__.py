from flask import current_app as app, render_template, Blueprint

bp = Blueprint(
    'home_bp', __name__,
        static_folder='./static',
        template_folder='./templates',
        url_prefix=''
)


@bp.route('/', methods=['GET'])
@bp.route('/index', methods=['GET'])
@bp.route('/home/', methods=['GET'])
def home():
    """home page."""
    return render_template(
        'home.html',
        style_bundle_name="home_bp_styles",
        js_bundle_name="home_bp_js",
        title="Jinja Demo Site",
        description="Smarter page templates with Flask & Jinja.")
