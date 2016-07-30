# coding: utf-8
from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class SearchForm(Form):
    search = StringField('search', validators=[
                         DataRequired(), Length(
                                        max=100,
                                        message=(u'太长？太短？改一下关键词吧'))
                         ])
