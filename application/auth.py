from flask import current_app as app, flash, redirect, url_for, session, request
from .models import db, Users
from flask_login import login_user, logout_user, current_user
from . import login_manager, esisecurity
from esipy.exceptions import APIException
from sqlalchemy.orm.exc import NoResultFound
import random, hmac, hashlib

# -----------------------------------------------------------------------
# Flask Login requirements
# -----------------------------------------------------------------------
@login_manager.user_loader
def load_user(character_id):
    """ Required user loader for Flask-Login """
    if character_id is not None:
        return Users.query.get(character_id)
    return None

@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view that page.')
    return redirect(url_for('evelogin'))

# @auth_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     """
#     Log-in page for registered users.

#     GET requests serve Log-in page.
#     POST requests validate and redirect user to dashboard.
#     """
#     # Bypass if user is logged in
#     if current_user.is_authenticated:
#         return redirect(url_for('main_bp.dashboard'))

#     form = LoginForm()
#     # Validate login attempt
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user and user.check_password(password=form.password.data):
#             login_user(user)
#             next_page = request.args.get('next')
#             return redirect(next_page or url_for('main_bp.dashboard'))
#         flash('Invalid username/password combination')
#         return redirect(url_for('auth_bp.login'))
#     return render_template(
#         'login.jinja2',
#         form=form,
#         title='Log in.',
#         template='login-page',
#         body="Log in with your User account."
#     )

def gen_state_token():
    """Generates a non-guessable OAuth token"""
    chars = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    rand = random.SystemRandom()
    random_string = ''.join(rand.choice(chars) for _ in range(40))
    return hmac.new(
        app.config.get('ESI_SECRET_KEY').encode('utf-8'),
        random_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

@app.route('/evelogin')
def login():
    state_token = gen_state_token()
    session['token'] = state_token
    auth_uri = r'https://login.eveonline.com/v2/oauth/authorize?response_type=code&redirect_uri=%s&client_id=%s%s%s' % (
        app.config.ESI_CALLBACK,
        app.config.ESI_CLIENT_ID,
        '&scope=%s' % ' '.join(app.config.ESI_SCOPES),
        '&state=%s' % state_token
    )
    return redirect(auth_uri)


@app.route('/sso/callback')
def callback():
    """ This is where the user comes after he logged in SSO """
    # get the code from the login process
    code = request.args.get('code')
    token = request.args.get('state')

    # compare the state with the saved token for CSRF check
    sess_token = session.pop('token', None)
    if sess_token is None or token is None or token != sess_token:
        return 'Login EVE Online SSO failed: Session Token Mismatch', 403

    # now we try to get tokens
    try:
        auth_response = esisecurity.auth(code)
    except APIException as e:
        return 'Login EVE Online SSO failed: %s' % e, 403

    # we get the character informations
    cdata = esisecurity.verify()

    # if the user is already authed, we log him out
    if current_user.is_authenticated:
        link_token = session.pop('link', None)
        if link_token is not None:
            current_user.link_token = link_token
            db.session.commit()
        logout_user()

    # now we check in database, if the user exists
    # actually we'd have to also check with character_owner_hash, to be
    # sure the owner is still the same, but that's an example only...
    try:
        user = Users.query.filter(
            Users.character_id == cdata['sub'].split(':')[2],
        ).one()

    except NoResultFound:
        user = Users()
        user.character_id = cdata['sub'].split(':')[2]

    user.character_owner_hash = cdata['owner']
    user.character_name = cdata['name']
    if current_user.is_authenticated:
        if link_token is not None:
                user.link_token = link_token
    user.update_token(auth_response)

    # now the user is ready, so update/create it and log the user
    try:
        db.session.merge(user)
        db.session.commit()
        login_user(user)
        session.permanent = True
    except:
        # logger.exception("Cannot login the user - uid: %d" % user.character_id)
        db.session.rollback()
        logout_user()

    return redirect(url_for('home_bp.home'))