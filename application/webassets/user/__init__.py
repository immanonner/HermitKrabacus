from flask import current_app as app, render_template, Blueprint
from flask_login import current_user, login_required
from numpy import character
from application import esiapp, esiclient
from sqlalchemy import null


bp = Blueprint(
    'user_bp', __name__,
        static_folder='./static',
        template_folder='./templates',\
        url_prefix='/user')


# get eve online user information such as wallet, characters, etc.
def get_user_eve_info():
    toons = []
    if current_user.link_token and current_user.link_token != null:
        toons = [toon for toon in current_user.linked_characters() if toon != current_user]
    toons.append(current_user)  
    op = esiapp.op['get_characters_character_id_wallet'](
                character_id=current_user.character_id
            )
    op = esiapp.op['get_characters_character_id_orders'](
            character_id=current_user.character_id,
            token=current_user.access_token
        )
    op = esiapp.op['get_characters_character_id_wallet_transactions'](character_id=current_user.character_id,
                                                                    token=current_user.access_token)
    pass



@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """user dashboard."""
    return render_template(
        'dashboard.html',
        characters = get_user_eve_info(),
        title=f"Hermit Krabacus Dashboard - {current_user.character_name}",
        description="Overview of User's account and your current settings."
        )

