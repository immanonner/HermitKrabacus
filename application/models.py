import time
from datetime import datetime

from flask_login import UserMixin
from sqlalchemy import null, ForeignKey

from . import db

# -----------------------------------------------------------------------
# Database models
# -----------------------------------------------------------------------


class Users(db.Model, UserMixin):
    # our ID is the character ID from EVE API
    __tablename__ = 'users'
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
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.character_name}: {self.character_id}>'

    def get_id(self):
        """ Required for flask-login """
        return self.character_id

    def linked_characters(self) -> list:
        """ helper function to get all linked characters """
        if self.link_token is null or self.link_token is None:
            return [self]
        else:
            return self.query.filter_by(link_token=self.link_token).all()

    def get_sso_data(self):
        """ Little "helper" function to get formated data for esipy security"""
        return {
            'access_token':
                self.access_token,
            'refresh_token':
                self.refresh_token,
            'expires_in':
                (self.access_token_expires - datetime.utcnow()).total_seconds()
        }

    def update_token(self, token_response):
        """ helper function to update token data from SSO response """
        self.access_token = token_response['access_token']
        self.access_token_expires = datetime.fromtimestamp(
            time.time() + token_response['expires_in'],)
        if 'refresh_token' in token_response:
            self.refresh_token = token_response['refresh_token']

    def clear_esi_tokens(self):
        """ helper function to clear token data """
        self.access_token = None
        self.access_token_expires = None
        self.refresh_token = None


class InvTypes(db.Model):
    __tablename__ = 'invTypes'
    typeID = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    groupID = db.Column(db.BigInteger, autoincrement=False)
    typeName = db.Column(db.String(999))
    description = db.Column(db.String(9000), nullable=True)
    mass = db.Column(db.Float)
    volume = db.Column(db.Float)
    capacity = db.Column(db.Float)
    portionSize = db.Column(db.BigInteger)
    raceID = db.Column(db.BigInteger, nullable=True)
    basePrice = db.Column(db.Float, nullable=True)
    published = db.Column(db.Boolean)
    marketGroupID = db.Column(db.BigInteger, nullable=True)
    iconID = db.Column(db.BigInteger, nullable=True)
    soundID = db.Column(db.BigInteger, nullable=True)
    graphicID = db.Column(db.BigInteger)

    invVolumes = db.relationship('InvVolumes',
                                 backref="invVolumes",
                                 uselist=False)

    def __repr__(self):
        return f'<Item {self.typeID}: {self.typeName}>'


class InvVolumes(db.Model):
    __tablename__ = 'invVolumes'
    typeID = db.Column(db.BigInteger,
                       ForeignKey(InvTypes.typeID),
                       primary_key=True,
                       autoincrement=False)
    packVolume = db.Column(db.Float)

    def __repr__(self):
        return f'<{self.typeID} Packed Volume: {self.volume}>'


class SolarSystems(db.Model):
    __tablename__ = 'solarSystems'
    regionID = db.Column(db.BigInteger)
    constellationID = db.Column(db.BigInteger)
    solarSystemID = db.Column(db.BigInteger,
                              primary_key=True,
                              autoincrement=False)
    solarSystemName = db.Column(db.String(100))
    security = db.Column(db.Float)
    securityClass = db.Column(db.String(2))
    structureMarkets = db.relationship('StructureMarkets',
                                       back_populates="solarSystems")

    def __repr__(self):
        return f'<{self.solarSystemName} ID: {self.solarSystemID}>'


class StructureMarkets(db.Model):
    __tablename__ = 'structureMarkets'
    struc_id = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    name = db.Column(db.String(100))
    typeID = db.Column(
        db.BigInteger,
        ForeignKey(InvTypes.typeID),
    )
    solarSystemID = db.Column(
        db.BigInteger,
        ForeignKey(SolarSystems.solarSystemID),
    )
    sell_orders = db.Column(db.PickleType(), nullable=True)
    sell_orders_expiry = db.Column(db.DateTime(), nullable=True)
    history = db.Column(db.PickleType(), nullable=True)
    history_expiry = db.Column(db.DateTime(), nullable=True)

    invTypes = db.relationship('InvTypes', backref="invTypes", uselist=False)
    solarSystems = db.relationship('SolarSystems',
                                   back_populates="structureMarkets")

    def __repr__(self) -> str:
        return f'<{self.name} Market Data Expires: {self.expiry}>'

    def is_expired(self, cache_date) -> bool:
        if cache_date is None:
            return True
        epoch = datetime(1970, 1, 1)
        # this date is ALWAYS in UTC (RFC 7231)
        expires_in = (cache_date - epoch).total_seconds()
        now = (datetime.utcnow() - epoch).total_seconds()
        return int(expires_in) - int(now) <= 0

    def update_history_records(self, records: list[dict]):
        self.history = records
        self.history_expiry = self.__pull_earliest_exp_date(records)

    def update_sell_orders(self, orders: list[dict]):
        self.sell_orders = orders
        self.sell_orders_expiry = self.__pull_earliest_exp_date(orders)

    def __pull_earliest_exp_date(self, records) -> datetime:
        uniq_dates = {
            rec['expires'] for rec in records if rec.get('expires', None)
        }
        if len(uniq_dates) == 1:
            return datetime.strptime(
                list(uniq_dates)[0], '%a, %d %b %Y %H:%M:%S %Z')
        else:
            earliest = datetime.datetime(9999, 12, 31, 23, 59, 999999)
            for d in uniq_dates:
                parsed_date = datetime.strptime(d, '%a, %d %b %Y %H:%M:%S %Z')
                if parsed_date < earliest:
                    earliest = parsed_date
            return earliest