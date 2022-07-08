import os

from flask import Blueprint


def all_blueprints():
    """Import all blueprints for application."""
    not_registered_bps = []
    for path in os.scandir(os.path.dirname(__file__)):
        if path.is_dir() and '__init__.py' in os.listdir(path):
            module_name = f'{__name__}.{path.name}'
            mod = __import__(module_name, fromlist=['bp'])
            not_registered_bps.append(mod.bp)
    return not_registered_bps
