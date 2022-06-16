"""Compile static assets."""
import os

from webassets import Bundle, Environment

assets = Environment(
    directory='application/webassets',
    url='/static', cache=False, manifest=False)

def compile_static_assets(assets: Environment, default_bp_name: str=None):
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
            -build/compile/transpile files

    """
    for dr in os.scandir(assets.directory):
        if "." not in dr.name and dr.is_dir():
            if default_bp_name is not None and dr.name != default_bp_name:
                js_bundle_path_arg =[f'{default_bp_name}/static/*.js', f'{dr.name}/static/*.js']
                less_bundle_path_arg = [p.replace("*.js","*.less") for p in js_bundle_path_arg]
            else:
                js_bundle_path_arg = [f'{dr.name}/static/*.js']
                less_bundle_path_arg = [f'{dr.name}/static/*.less']

            js_bundle = assets.register(f'{dr.name}_js',
                Bundle(
                        *js_bundle_path_arg,
                        filters='jsmin',
                        output=f'{dr.name}/static/dist/{dr.name}.min.js'))

            less_bundle = assets.register(f'{dr.name}_styles',
                Bundle(
                        *less_bundle_path_arg,
                        filters='less,cssmin',
                        output=f'{dr.name}/static/dist/{dr.name}.min.css',))


            js_bundle.build()
            less_bundle.build()

if __name__ == '__main__':
    compile_static_assets(assets, default_bp_name="base")

