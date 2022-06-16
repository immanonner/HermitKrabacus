import pathlib


def make_blank_webpage(page_name, login_required=False):
    """
    Create a blank webpage directory and boilerplate code.
    """
    page_dir = f"application/webassets/{page_name}"

    pathlib.Path(page_dir).mkdir(parents=True, exist_ok=False)
    with open(page_dir + "/__init__.py", 'w') as f:
        f.write(f'''\
from flask import Blueprint, render_template
{"from flask_login import current_user, login_required" if login_required else ""}

bp = Blueprint(
    '{page_name}_bp', __name__,
        static_folder='./static',
        template_folder='./templates',
        url_prefix='/{page_name}')


@bp.route('/{page_name}', methods=['GET'])
{"@login_required" if login_required else ""}
def {page_name}():
    # {page_name}
    return render_template(
        '{page_name}.html',
        title="{page_name} title",
        description="{page_name} description",)      
''')

    templates_dir = f"{page_dir}/templates"
    pathlib.Path(templates_dir).mkdir(parents=True, exist_ok=False)
    with open(templates_dir + f"/{page_name}.html", 'w') as f:
        f.write('''\
{% extends 'layout.html' %}

{% block content %}
<div class="container">
    <h1>{{title}}</h1>
    <p>{{description}}</p>
</div>
{% endblock %}         
''')
    static_dir = f"{page_dir}/static"
    pathlib.Path(static_dir).mkdir(parents=True, exist_ok=False)
    pathlib.Path(static_dir + f"/{page_name}.js").touch()
    pathlib.Path(static_dir + f"/{page_name}.less").touch()


if __name__ == "__main__":
    input_page_name = input("Enter the name of the new webpage: ")
    input_login_required = input("Login required? (y/n): ")
    if input_login_required == "y":
        make_blank_webpage(input_page_name, login_required=True)
    else:
        make_blank_webpage(input_page_name)
