from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from application.models import SolarSystems


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SelectForm(SearchForm):
    select = SelectField(choices=SolarSystems.get_solarsystems(null_sec=False))