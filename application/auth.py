from flask import current_app as app, flash, redirect, url_for, session, request
from sqlalchemy import null
from .models import db, Users
from flask_login import login_user, logout_user, current_user, login_required
from . import login_manager, esiclient, esisecurity
from esipy.exceptions import APIException
from sqlalchemy.exc import NoResultFound
import random, hmac, hashlib


# -----------------------------------------------------------------------
# Flask Login requirements
# -----------------------------------------------------------------------
@login_manager.user_loader
def load_user(character_id):
    """ Required user loader for Flask-Login """
    if character_id is not None:
        toon = Users.query.get(character_id)
        if toon is not None:
            esisecurity.update_token(toon.get_sso_data())
            if esisecurity.is_token_expired() :
                try:
                    # refresh token
                    # todo: verify owner hash is the same - necessary?
                    fresh_esi_tokens = esisecurity.refresh()
                    toon.update_token(fresh_esi_tokens)
                    db.session.commit()
                    return toon
                except (APIException, AttributeError):
                    # refresh token failed, delete token
                    toon.clear_esi_tokens()
                    db.session.commit()
                    return None
        return None           
    return None

@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    return redirect(url_for('login'))


def gen_state_token(length=40):
    """Generates a non-guessable OAuth token"""
    chars = ('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    rand = random.SystemRandom()
    random_string = ''.join(rand.choice(chars) for _ in range(length))
    return hmac.new(
        app.config.get('ESI_SECRET_KEY').encode('utf-8'),
        random_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
@app.route('/evelogout')
@login_required
def logout(switch=False):
    logout_user()
    flash('Successfully logged out!', 'success')
    switch = bool(request.args.get("switch"))
    if switch:
        return redirect(url_for('login', switch=False))
    return redirect(url_for("home_bp.home"))

@app.route('/evelogin')
def login(link=False, switch=False):
    link = bool(request.args.get("link"))
    switch = bool(request.args.get("switch"))
    if switch and current_user.is_authenticated:
        return redirect(url_for("logout", switch=True))
    if not current_user.is_anonymous and link is True:
        if current_user.link_token is None or current_user.link_token is null:
            link_token = gen_state_token(length=16)
            current_user.link_token = link_token
            db.session.commit()
        else:
            link_token = current_user.link_token    
        session['link_token'] = link_token
    state_token = gen_state_token()
    session['token'] = state_token
    auth_uri = r'https://login.eveonline.com/v2/oauth/authorize?response_type=code&redirect_uri=%s&client_id=%s%s%s' % (
        app.config.get('ESI_CALLBACK'),
        app.config.get('ESI_CLIENT_ID'),
        '&scope=%s' % ' '.join(app.config.get('ESI_SCOPES')),
        '&state=%s' % state_token)
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
        auth_response = esiclient.security.auth(code)
    except APIException as e:
        return 'Login EVE Online SSO failed: %s' % e, 403

    # we get the character informations
    cdata = esisecurity.verify()

    # if the user is already authed, we log him out
    if current_user.is_authenticated:
        logout_user()

    # now we check in database, if the user exists
    # actually we'd have to also check with character_owner_hash, to be
    # sure the owner is still the same, but that's an example only...
    # todo: verify owner hash is the same even necessary?
    try:
        user = Users.query.filter(
            Users.character_id == cdata['sub'].split(':')[2],
            ).one()
    
    except NoResultFound:
        user = Users()
        user.character_id = cdata['sub'].split(':')[2]
        user.character_name = cdata['name']
    user.character_owner_hash = cdata['owner']
    if session.get('link_token', None) != None:
        user.link_token = session.pop('link_token')
    user.update_token(auth_response)

    # now the user is ready, so update/create it and log the user
    try:
        db.session.merge(user)
        db.session.commit()
        login_user(user)
        session.permanent = True
    except:
        db.session.rollback()
        logout_user()

    return redirect(url_for('user_bp.dashboard'))