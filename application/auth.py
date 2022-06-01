

# -----------------------------------------------------------------------
# Flask Login requirements
# -----------------------------------------------------------------------
@login_manager.user_loader
def load_user(character_id):
    """ Required user loader for Flask-Login """
    return Users.query.get(character_id)