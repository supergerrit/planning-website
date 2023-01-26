from django import forms


class MatCheckbox(forms.widgets.CheckboxInput):
    template_name = "mat_checkbox.html"


class DateInput(forms.DateInput):
    input_type = 'date'
    # format = '%Y-%m-%d'


class TimeInput(forms.TimeInput):
    input_type = 'time'
    format = '%H:%M'

