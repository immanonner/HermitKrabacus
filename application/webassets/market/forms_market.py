from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from .esi_market import get_solarsystems


class SearchForm(FlaskForm):
    search = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Submit')


class SelectForm(SearchForm):
    select = SelectField(choices=get_solarsystems(null_sec=False))