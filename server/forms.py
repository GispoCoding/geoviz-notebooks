import sys
#from flask_admin.contrib.geoa.widgets import LeafletWidget
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, URL
from wtforms.widgets import CheckboxInput, HTMLString, ListWidget, TextInput

# test simple import now, convert to module later
sys.path.insert(0, "..")
from datasets import DATASETS


class LeafletWidget(TextInput):
    """
    Render bbox input using city name, map and bbox
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        city_name_html = '<input %s>' % self.html_params(name=field.name + '_city', **kwargs)
        map_html = '<div id="bbox_map" style="width: 600 px; height: 600px;"></div>'
        instructions_html = '<p>Adjust the coordinates on the map or below, if needed.</p>'
        bbox_html = '<input %s>' % self.html_params(name=field.name, **kwargs)
        return HTMLString(city_name_html + map_html + instructions_html + bbox_html)


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class CitySelectionField(StringField):
    """
    A fancy Leaflet field that returns a bbox selected by the user.
    """
    widget = LeafletWidget()


class AnalysisForm(FlaskForm):
    dataset_selection = MultiCheckboxField(
        'Select data to include in the analysis',
        choices=DATASETS
    )
    gtfs_url = StringField(
        'GTFS feed location for the city',
        [URL(message='Please input a valid GTFS URL.')]
    )
    flickr_apikey = StringField('API key for flickr API')
    mapbox_apikey = StringField('API key for Mapbox')

    bbox = CitySelectionField('City area to analyze')

    import_button = SubmitField('Import datasets')
