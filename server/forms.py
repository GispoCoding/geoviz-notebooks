import sys
#from flask_admin.contrib.geoa.widgets import LeafletWidget
from flask_wtf import FlaskForm
from markupsafe import Markup
from wtforms import SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, URL
from wtforms.widgets import html_params, CheckboxInput, HTMLString, ListWidget, TextInput

# test simple import now, convert to module later
sys.path.insert(0, "..")
from datasets import DATASETS


class LeafletWidget(TextInput):
    """
    Render bbox input using city name autocomplete field, map and bbox
    """

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()
        city_name_kwargs = {
            'id': 'city_search',
            'name': field.name + '_city',
            'type': self.input_type,
            'autocomplete': 'off'
            }
        city_name_html = 'Type the name of the city, or click on the map to select a specific neighborhood <input %s>' % self.html_params(**city_name_kwargs)

        map_html = '<div id="bbox_map" style="width: 400 px; height: 400px"></div>'
        instructions_html = '<p>Adjust the bounding box on the map, if needed</p>'
        bbox_html = '<input %s readonly>' % self.html_params(name=field.name, **kwargs)
        return HTMLString(map_html + city_name_html + instructions_html + bbox_html)


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

    bbox = CitySelectionField()

    import_button = SubmitField('Import datasets')
