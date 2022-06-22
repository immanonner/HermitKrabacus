# get each linked eve online user information such as wallet, characters, etc.
from concurrent.futures import ThreadPoolExecutor

from application import esiapp, esiclient
from application.models import Users, invTypes, invVolumes, SolarSystems, db
from config import *
from esipy import EsiClient, EsiSecurity
from esipy.exceptions import APIException
from flask import flash
from flask_login import current_user


def get_solarsystems() -> dict:

    return {
        rw[0]: rw[1] for rw in db.session.query(SolarSystems.solarSystemName,
                                                SolarSystems.solarSystemID)
    }
