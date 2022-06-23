from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class SolarSystemForm(FlaskForm):
    system_name = StringField('Search for Solar System',
                              validators=[DataRequired()])
    submit = SubmitField('Get System Structures')