"""Compile static assets."""
import os

from flask import current_app as app
from flask_assets import Bundle, Environment


def compile_static_assets(assets, default_bp_name=None):
    """ Configure and build static asset (js/css) bundles.
        bundle paths are relative the assets environment directory
        that env directory is relative to your flask app static directory <default>, or the static directory of a Flask blueprint.

        [assumed static file structure]
        static
            -<bundle_name>
                - dist/
                    -min.css
                    -min.js
                <src>.js
                <src>.less
            -<bundle_name>

        loop explanation:
        - grab all relative dir names to blueprint static directory to use as bundle names
        - ensure that they are dirs and do not begin with "."
        - assemble path arguments for bundle input files
        - register bundles 
            -build/compile/transpile files if flask_env = dev
            refactor due to blueprints restructure.
            iter_blueprints()

    """
    for bp in app.iter_blueprints():
        if default_bp_name is not None and bp.name != default_bp_name:
            js_bundle_path_arg = [f'{default_bp_name}/*.js', f'{bp.name}/*.js']
            less_bundle_path_arg = [
                p.replace("*.js", "*.less") for p in js_bundle_path_arg
            ]
        else:
            js_bundle_path_arg = [f'{bp.name}/*.js']
            less_bundle_path_arg = [f'{bp.name}/*.less']

        js_bundle = assets.register(
            f'{bp.name}_js',
            Bundle(*js_bundle_path_arg,
                   filters='jsmin',
                   output=f'{bp.name}/dist/{bp.name.replace("_bp","")}.min.js'))

        less_bundle = assets.register(
            f'{bp.name}_styles',
            Bundle(
                *less_bundle_path_arg,
                filters='less,cssmin',
                output=f'{bp.name}/dist/{bp.name.replace("_bp","")}.min.css',
            ))

        if os.environ['FLASK_ENV'] == 'development':
            js_bundle.build()
            less_bundle.build()
