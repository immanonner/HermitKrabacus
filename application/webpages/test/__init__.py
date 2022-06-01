from flask import current_app as app, render_template, Blueprint

bp = Blueprint(
    'test_bp', __name__,
        static_folder='./static',
        template_folder='./templates',\
        url_prefix='/test')


@bp.route('/', methods=['GET'])
def test():
    """test page."""
    return render_template(
        'test.html',
        style_bundle_name="test_bp_styles",
        js_bundle_name="test_bp_js",
        title="test",
        description="Smarter page templates with Flask & Jinja.")
