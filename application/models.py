from . import db
from datetime import datetime
import time
from flask_login import UserMixin

# -----------------------------------------------------------------------
# Database models
# -----------------------------------------------------------------------

class Users(db.Model, UserMixin):
    # our ID is the character ID from EVE API
    character_id = db.Column(db.BigInteger,
        primary_key=True,
        autoincrement=False)
    character_name = db.Column(db.String(200))
    # EVE SSO Token stuff
    access_token_expires = db.Column(db.DateTime())
    character_owner_hash = db.Column(db.String(255))
    refresh_token = db.Column(db.String(100))
    access_token = db.Column(db.String(4096))
    # Token that associates this user with other toons
    link_token = db.Column(db.String(100), nullable=True)
    # overshadow the USERMIXIN get_id method with our own
    def get_id(self):
        """ Required for flask-login """
        return self.character_id
    
    def linked_characters(self):
        """ helper function to get all linked characters """
        return self.query.filter_by(link_token=self.link_token).all()

    def get_sso_data(self):
        """ Little "helper" function to get formated data for esipy security
        """
        return {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'expires_in': (self.access_token_expires - datetime.utcnow()).total_seconds()
        }

    def update_token(self, token_response):
        """ helper function to update token data from SSO response """
        self.access_token = token_response['access_token']
        self.access_token_expires = datetime.fromtimestamp(
            time.time() + token_response['expires_in'],)
        if 'refresh_token' in token_response:
            self.refresh_token = token_response['refresh_token']
    