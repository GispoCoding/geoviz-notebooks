import sys
#from flask_admin.contrib.geoa.widgets import LeafletWidget
from flask_wtf import FlaskForm
from markupsafe import Markup
from sqlalchemy.sql.sqltypes import String
from wtforms import Field, FormField, SelectMultipleField, StringField, SubmitField
from wtforms.fields.core import Field
from wtforms.validators import DataRequired, Length, Optional, URL
from wtforms.widgets import html_params, CheckboxInput, ListWidget

# test simple import now, convert to module later
sys.path.insert(0, "..")
from datasets import DATASETS


class LeafletWidget(object):
    def __call__(self, field, **kwargs):
        return Markup('<div id="bbox_map" style="width: 400 px; height: 400px"></div><br>')


class CheckboxListWidget(ListWidget):
    """
    Renders a list of fields as a `ul` or `ol` list.

    A variation of CheckboxListWidget that renders checkboxes inside labels
    for Materialize styling.

    If `prefix_label` is set, the subfield's label is printed before the field,
    otherwise afterwards. The latter is useful for iterating radios or
    checkboxes.
    """
    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<%s %s>' % (self.html_tag, self.html_params(**kwargs))]
        for subfield in field:
            if self.prefix_label:
                html.append('<li><label for=%s><span>%s</span> %s</label></li>' %
                            (subfield.id, subfield.label.text, subfield()))
            else:
                html.append('<li><label for=%s>%s <span>%s</span></label></li>' %
                            (subfield.id, subfield(), subfield.label.text))
        html.append('</%s>' % self.html_tag)
        return Markup(''.join(html))


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = CheckboxListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class LeafletField(Field):
    """
    Does nothing. Contains map.
    """
    widget = LeafletWidget()


class CitySelectionForm(FlaskForm):
    map = LeafletField()
    city = StringField(
        'Type the name of the city, or click on the map to select a specific neighborhood',
        [DataRequired]
        )
    bbox = StringField(
        'Adjust the bounding box on the map, if needed',
        [DataRequired]
        )


class AnalysisForm(FlaskForm):
    dataset_selection = MultiCheckboxField(
        'Select data to include in the analysis',
        [DataRequired],
        choices=DATASETS
    )
    gtfs_url = StringField(
        'GTFS feed location for the city',
        [Optional, URL(message='Please input a valid GTFS URL.')]
    )
    flickr_apikey = StringField('API key for flickr API')
    mapbox_apikey = StringField('API key for Mapbox')

    bbox = FormField(CitySelectionForm)

    import_button = SubmitField('Import datasets')
